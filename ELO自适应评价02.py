import tkinter as tk
from PIL import Image, ImageTk
import os
import random
import pandas as pd
import time
from tkinter import font as tkfont
from tkinter import messagebox

class ImageComparer:
    def __init__(self, master):
        self.master = master
        master.title("Image Comparison Tool")
        self.master.geometry("2020x1080")  # 设置窗口大小
        self.image_dir = '01源图像'
        self.image_paths = os.listdir(self.image_dir)
        self.image_scores = {img: 1000 for img in self.image_paths}  # 初始化Elo评分
        self.last_chosen = {img: time.time() for img in self.image_paths}  # 初始化选择时间
        self.recently_shown = []  # 存储最近显示的图片
        self.recent_limit = 10  # 控制重复图片的显示间隔
        self.data = []
        self.round = 0  # 记录回合数
        self.previous_ranks = {img: idx + 1 for idx, img in
                               enumerate(sorted(self.image_scores, key=self.image_scores.get, reverse=True))}

        # 添加标题，并应用自定义字体
        self.title_font = tkfont.Font(family='Times New Roman', size=24, weight="bold")
        self.label = tk.Label(master, text="Which of the two images below do you find more attractive?", font=self.title_font)
        self.label.pack()
        self.load_images()

        # 结束按钮
        self.quit_button = tk.Button(master, text="结束测试", command=self.finish)
        self.quit_button.pack(side="bottom")

    def load_images(self):
        if len(self.image_paths) < 2:
            print("Not enough images.")
            return

        # 自适应选择逻辑，避免最近显示的图片立即重复出现
        available_paths = [p for p in self.image_paths if p not in self.recently_shown]
        if len(available_paths) < 2:
            available_paths = self.image_paths[:]  # 如果可用图片不足，则重置
            self.recently_shown.clear()

        self.current_pair = random.sample(available_paths, 2)
        self.images = [Image.open(os.path.join(self.image_dir, path)) for path in self.current_pair]
        self.display_images()
        # 更新最近显示的图片列表
        self.recently_shown.extend(self.current_pair)
        if len(self.recently_shown) > self.recent_limit:
            self.recently_shown = self.recently_shown[-self.recent_limit:]

    def display_images(self):
        max_height = 770
        self.img_labels = []
        for i, img in enumerate(self.images):
            img_ratio = img.width / img.height
            new_height = max_height
            new_width = int(new_height * img_ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            label = tk.Label(self.master, image=tk_img)
            label.image = tk_img  # Keep a reference!
            label.bind("<Button-1>", lambda event, idx=i: self.choose_image(idx))
            label.pack(side="left")
            self.img_labels.append(label)

    def choose_image(self, chosen_index):
        chosen = self.current_pair[chosen_index]
        not_chosen = self.current_pair[1 - chosen_index]
        self.update_scores(chosen, not_chosen)
        self.last_chosen[chosen] = time.time()  # 更新时间戳
        self.update_rank_data(chosen, not_chosen)
        self.refresh_images()
        self.round += 1  # 更新回合数
        if self.round >= 2000:
            self.finish()
            messagebox.showinfo("实验结束", "感谢您对本次测试的贡献❥(^_-)！")

    def update_scores(self, winner, loser):
        K = 32  # Elo rating K-factor
        winner_score = self.image_scores[winner]
        loser_score = self.image_scores[loser]
        expected_winner = 1 / (1 + 10 ** ((loser_score - winner_score) / 400))
        expected_loser =1 / (1 + 10 ** ((winner_score - loser_score) / 400))
        self.image_scores[winner] += K * (1 - expected_winner)
        self.image_scores[loser] -= K * (expected_loser)

    def update_rank_data(self, chosen, not_chosen):
        # 获取对比后的排名
        current_ranks = {img: rank for rank, img in
                         enumerate(sorted(self.image_scores, key=self.image_scores.get, reverse=True), 1)}
        # 计算 Rank_diff
        n = len(self.image_paths)
        rank_diff = sum(abs(current_ranks[img] - self.previous_ranks[img]) for img in self.image_paths) / n
        self.previous_ranks = current_ranks
        # 记录 Rank_diff 以及选择的和未选择的图片
        self.data.append((self.current_pair[0], self.current_pair[1], chosen, not_chosen, rank_diff))

    def refresh_images(self):
        for label in self.img_labels:
            label.pack_forget()
        self.load_images()

    def finish(self):
        # 保存选择数据
        results_df = pd.DataFrame(self.data, columns=['Image1', 'Image2', 'Chosen', 'NotChosen', 'Rank_diff'])
        results_df.to_csv('results.csv', index=False)

        # 生成最终的排名数据
        rank_data = pd.DataFrame(list(self.image_scores.items()), columns=['Image', 'Final Score'])
        rank_data.to_excel('rankings.xlsx', index=False)
        print("Test finished. Results saved.")
        self.master.quit()

root = tk.Tk()
app = ImageComparer(root)
root.mainloop()
