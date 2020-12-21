#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/12/17 8:11
# @Author  : shadow
# @Site    : 
# @File    : conver.py
# @Descript: get audio from video or Conver video format

from tkinter import Label, Button, Entry, Checkbutton, Listbox, Scrollbar, StringVar, IntVar, Tk, Canvas, W, NS
from tkinter.ttk import Combobox
from threading import Thread
import tkinter.filedialog as filedialog
from tkinter.messagebox import showwarning, askyesno
from moviepy.editor import VideoFileClip, CompositeVideoClip
from queue import Queue
import time
import os

video_type = {"mp4": "mp4v", "avi": "XVID"}
audio_type = {"mp3": "mp3", "wav": "wav"}


class ConverThread(Thread):
    def __init__(self, video_in, out, only):
        Thread.__init__(self)
        self.video_in = video_in
        self.out = out
        self.audio_only = only
        self.video = video_in.rsplit('\\', 1)[-1]

    def run(self):
        if os.path.exists(self.out):
            if not askyesno("警告", f"文件已存在，是否覆盖文件\n{self.out}"):
                percent_update(msg="跳过 "+self.video)
                return

        videoclip = VideoFileClip(self.video_in)
        try:
            if self.audio_only:
                videoclip.audio.write_audiofile(self.out)
                percent_update(msg=f"Get {self.video} success!")
            else:
                videoclip2 = videoclip.set_audio(videoclip.audio)
                video = CompositeVideoClip([videoclip2])
                # video.write_videofile(self.out, codec='mpeg4')
                video.write_videofile(self.out, codec='libx264')
                percent_update(msg=f"{self.video} conver success!")
        except Exception as e:
            showwarning("错误", f"处理文件[{self.video}]出错\n{repr(e)}")
            percent_update(msg=f"{self.video} conver fail!")


class Conver:
    def __init__(self, path_in, path_out, videos):
        self.audio_only = False
        self.run = False
        self.path_in = path_in
        self.path_out = path_out
        self.video_list = videos
        self.wildcard = ".avi .mp4 .mpg .rmvb"

    def get_video(self):
        # 选择要处理的文件路径
        # path = filedialog.askopenfile(title='Select video directory', filetypes=[('video', '*.avi'),
        #                             ('video', '*.mp4'), ('video', '*.rmvb'), ('All Files', '*')]).name
        path = filedialog.askdirectory(title='Select video directory', mustexist=True)
        if not path and not self.video_list.get():
            showwarning("Warning", "请选择视频所在文件夹")
            return
        print(path)
        self.path_in.set(path)
        self.path_out.set(path + "/new/")

        # 获取对应文件夹下所有符合要求的视频文件并写入listbox
        files = get_files_from_dir(path, self.wildcard)
        self.video_list.set(files)
        listbox_label["listvariable"] = video_list

    def conver(self):
        time.sleep(1)  # 等待队列先添加
        while True:
            if not video_queue.empty():
                video_in, video_out = video_queue.get()
                print("do ", video_in.rsplit('\\', 1)[-1])
                video = ConverThread(video_in, video_out, self.audio_only)
                video.setDaemon(True)
                video.start()
                # video.join()
            else:
                break

    def conver_video(self, files):
        Thread(target=self.conver, daemon=True).start()
        conver.run = True
        for file in files:
            path_in = os.path.join(in_path.get(), file)  # 输入文件
            path_out = out_path.get()
            if not os.path.exists(path_out):  # 判断是否存在文件夹如果不存在则创建为文件夹
                os.makedirs(path_out)

            file = file.rsplit(".", 1)[0] + '.' + cb_video["values"][cb_video.current()]
            # print(file)
            path_out = os.path.join(path_out, file)  # 输出文件
            video = path_in, path_out
            video_queue.put(video)  # 添加到队列

    def is_run(self):
        if self.run:
            showwarning("警告", '程序正在运行中，请稍后再试...')
            return True
        return False

    def add_all(self):
        if not video_list.get():
            showwarning("警告", '请先选择视频所在文件夹')
            return
        if self.is_run():
            return

        files = eval(video_list.get())
        percent_update(total=len(files))  # 进度条初始化
        self.audio_only = audio_only.get()
        self.conver_video(files)

    def add_select(self):
        if self.is_run():
            return
        index = listbox_label.curselection()
        files = listbox_label.get(index)
        self.audio_only = audio_only.get()
        if self.audio_only:
            msg = f"是否要获取音频\n{files}"
        else:
            msg = f"是否要做视频转换\n{files}"
        if askyesno("处理", msg):
            percent_update()  # 进度条初始化
            self.conver_video([files])


def get_files_from_dir(src_dir, wildcard):
    file_names = []
    exts = wildcard.split(" ")
    files = os.listdir(src_dir)
    for name in files:
        fullname = os.path.join(src_dir, name)
        if os.path.isdir(fullname):
            # 遍历子路径，如果需要请修改pathStr获取方式，否者子路径的图片打开会有问题
            # file_names += get_files_from_dir(fullname, wildcard)
            pass
        else:
            for ext in exts:
                if name.endswith(ext):
                    file_names.append(name)
                    break
    return file_names


def percent_update(total=1, msg=None):
    now = 0
    if msg:
        now, total = list(map(int, bar_percent.get().split(r'/')))
        now += 1
        if now < total:
            bar_info["bar"].itemconfig(bar_info["text"], text=msg)
        else:
            bar_info["bar"].itemconfig(bar_info["text"], text="全部处理完成")
            conver.run = False
    else:
        bar_info["bar"].itemconfig(bar_info["text"], text='Waiting for video select...')

    bar_info["bar"].coords(bar_info["shape"], (0, 0, int(300 * (now/total)), 20))
    bar_percent.set(f'{now}/{total}')


def video_type_set():
    if audio_only.get():
        type_select.set("音频类型选择:")
        cb_video["values"] = list(audio_type.keys())
    else:
        type_select.set("视频类型选择:")
        cb_video["values"] = list(video_type.keys())
    cb_video.current(0)


if __name__ == '__main__':
    root = Tk()
    root.title("视频格式转换")
    root.geometry('510x452+200+200')  # 位置设置
    root.wm_resizable(False, False)  # 不允许修改长宽
    in_path = StringVar()
    out_path = StringVar()
    video_list = StringVar()
    bar_percent = StringVar()
    type_select = StringVar(value='视频类型选择:')
    audio_only = IntVar(value=0)
    video_queue = Queue(maxsize=3)  # 设置最多同时处理数量
    bar_info = {}

    conver = Conver(in_path, out_path, video_list)

    Label(root, text='源视频路径：').grid(row=0, column=0)
    Label(root, text='新视频路径：').grid(row=1, column=0, pady=6)
    Entry(root, textvariable=in_path, width=35, justify="left").grid(row=0, column=1, columnspan=3, sticky='W')
    Entry(root, textvariable=out_path, width=35, justify="left").grid(row=1, column=1, columnspan=3, sticky='W')
    Button(root, text='选择视频', background='blue', command=conver.get_video, height=2).grid(row=0, rowspan=2,
                                                                                          column=4, padx=8)

    # 视频、音频 格式
    Checkbutton(root, text="仅音频", variable=audio_only, command=video_type_set).grid(row=3, column=0, pady=5)
    Label(root, textvariable=type_select).grid(row=3, column=1)
    cb_video = Combobox(root, width=6)
    cb_video["values"] = list(video_type.keys())
    cb_video.grid(row=3, column=2, pady=5, sticky=W)
    cb_video.current(0)

    # 视频列表
    listbox_label = Listbox(root, height=14, width=40, selectbackground='red')
    listbox_label.grid(row=4, rowspan=3, column=0,  columnspan=3, pady=10)
    scrolly_h1 = Scrollbar(root, width=20, orient="vertical", command=listbox_label.yview)  # 纵向
    scrolly_h1.grid(row=4, rowspan=3, column=3, sticky=NS, pady=10)
    listbox_label['yscrollcommand'] = scrolly_h1.set
    listbox_label.bind('<Double-Button-1>', lambda event: conver.add_select())  # 双击选择单独转换

    # 执行按钮
    Button(root, text='全部处理', background='pink', command=conver.add_all, height=2).grid(row=5, column=4)

    # 进度条
    Label(root, text='转换进度：').grid(row=9, column=0)
    bar_info["bar"] = Canvas(root, width=300, height=20, bg="gray")
    bar_info["shape"] = bar_info["bar"].create_rectangle(0, 0, 0, 20, fill='green')
    bar_info["text"] = bar_info["bar"].create_text(150, 12, anchor='center')
    bar_info["bar"].itemconfig(bar_info["text"], text='Waiting for video select...')
    bar_info["bar"].grid(row=9, column=1, columnspan=3, pady=5)
    Label(root, textvariable=bar_percent).grid(row=9, column=4)

    root.mainloop()
