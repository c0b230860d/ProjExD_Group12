import os
import sys
import pygame as pg
from pygame.locals import *
import pygame.mixer
import time
import random
import math
import random

"""
以下、複数個のクラス等で参照回数が多いかつ、値の変化がないものを
グローバル変数とする
"""
# グローバル変数
WIDTH, HEIGHT = 1024, 768 # ディスプレイサイズ
FONT = "font/JF-Dot-MPlusS10.ttf"  # ドット文字細目
FONT_F = "font/JF-Dot-MPlusS10B.ttf"  # ドット文字太目
GRAVITY = 0.75  #重力の大きさ。ジャンプした時に落ちる力。

os.chdir(os.path.dirname(os.path.abspath(__file__)))

"""
画面のあたり判定に関する関数
"""
def check_bound1(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate

def check_bound2(obj_rct:pg.Rect) -> tuple[bool, bool]:
    """
    引数:ハートRect
    戻り値:タプル(横方向判定結果, 縦方向判定結果)
    行動範囲内ならTrue, 行動範囲外ならFalseを返す
    """
    yoko, tate = True, True
    if obj_rct.left < WIDTH/2-150+5 or WIDTH/2+150-5 < obj_rct.right:  # 横判定
        yoko = False
    if obj_rct.top < HEIGHT/2-50+5 or (HEIGHT/2-50)+300-5 < obj_rct.bottom:  # 縦判定
        tate = False
    return yoko, tate

def check_bound(obj_rct:pg.Rect, left:int, right:int, top:int, bottom:int) -> tuple[bool, bool]:
    """
    与えられた引数より外側にあるか否かを判断しそれに応じたTrue or Falseを返す
    引数1 obj_rct:判定したいオブジェクトのrect
    引数2 left:左側の座標
    引数3 right:右側の座標
    引数4 top:上の座標
    引数5 bottom:下の座標
    """
    yoko, tate = True, True
    if obj_rct.left < left or right < obj_rct.right:
        yoko = False
    if obj_rct.top < top or bottom < obj_rct.bottom:
        tate = False
    return yoko, tate

"""
プレイヤーを追従する際に使う関数(講義資料のまま)
"""
def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm

"""
以下のクラスは変更しなくてよい（初期設定）
開発する時はすべて折りたたんでおいた方がわかりやすいかも
"""
class Koukaton(pg.sprite.Sprite):
    """
    こうかとん表示に関するクラス
    """
    # img = pg.transform.rotozoom(
    #     pg.image.load("fig/dot_kk_negate.png"),
    #     0,1.5
    # )
    def __init__(self):
        """
        こうかとん画像Surfaceを生成する
        """
        super().__init__()
        self.images = [
            pg.transform.rotozoom(pg.image.load("fig/dot_kk_negate.png"), 0, 1.5),
            pg.transform.rotozoom(pg.image.load("fig/dot_kk_negate2.png"), 0, 1.5),
            pg.transform.rotozoom(pg.image.load("fig/dot_kk_negate3.png"), 0, 1.5),
            pg.transform.rotozoom(pg.image.load("fig/dot_kk_negate4.png"), 0, 1.5),
            pg.transform.rotozoom(pg.image.load("fig/dot_kk_negate3.png"), 0, 1.5),
            pg.transform.rotozoom(pg.image.load("fig/dot_kk_negate2.png"), 0, 1.5),
            pg.transform.rotozoom(pg.image.load("fig/dot_kk_negate.png"), 0, 1.5),
        ]
        self.image_index = 0
        self.image = self.images[self.image_index]
        # self.image = __class__.img
        self.rect: pg.Rect = self.image.get_rect()
        self.rect.center = WIDTH/2, HEIGHT/4+30
        self.frame_count = 0
        self.next = True
        self.tmr = 0

    def update(self, screen: pg.Surface):
        """
        こうかとんを表示
        引数1 screen：画面サーファイス
        """
        self.frame_count += 1
        if self.frame_count % 5 == 0 and self.next == True:  # フレームごとに切り替え速度を調整
            self.image_index = (self.image_index + 1) % len(self.images)
            self.image = self.images[self.image_index]
            if self.image_index == len(self.images)-1:
                self.next = False
        else:
            self.tmr += 1
            if self.tmr > 100:
                self.next = True
                self.tmr = 0
            
            
        screen.blit(self.image, self.rect)

    
class Heart(pg.sprite.Sprite):
    """
    プレイヤー（ハート）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img = pg.transform.rotozoom(
        pg.image.load("fig/Undertale_hurt.png"), 
        0, 0.02
        ) 
    invincible_time = 30  # 無敵時間
    
    def __init__(self, xy: tuple[int, int]):
        """
        ハート画像Surfaceを生成する
        引数 xy：ハート画像の初期位置座標タプル
        """
        super().__init__()
        self.image = __class__.img
        self.rect: pg.Rect = self.image.get_rect()
        self.rect.center = xy
        self.invincible = False

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてハートを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(sum_mv)
        if check_bound2(self.rect) != (True, True):
            self.rect.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.image = __class__.img
        if sum_mv != [0, 0]:
            self.dire = sum_mv
        if self.invincible:  # 無敵時間の設定
            if self.invincible_time == 0:
                self.invincible = False
                self.invincible_time = __class__.invincible_time
            else:
                self.invincible_time -= 1
                if self.invincible_time % 5 == 0:
                    screen.blit(self.image, self.rect)
        else:        
            screen.blit(self.image, self.rect)
            
        
class HeartGrav(pg.sprite.Sprite):
    """
    プレイヤー（ハート）に関するクラス
    """
    img = pg.transform.rotozoom(
        pg.image.load("fig/Undertale_hurt.png"), 
        0, 0.02
        )

    dx = 0  # x軸方向の移動量
    dy = 0  # y軸方向の移動量

    invincible_time = 30  # 無敵時間
    
    def __init__(self, xy: tuple[int, int]):
        """
        ハート画像Surfaceを生成する
        引数 xy：ハート画像の初期位置座標タプル
        """
        super().__init__()
        self.image = __class__.img
        self.rect: pg.Rect = self.image.get_rect()
        self.rect.center = xy

		# heartの移動スピードを代入
        self.speed = +5.0
		# Y軸方向の速度
        self.vel_y = 0
		# 空中にいるかどうかのフラグ
        self.in_air = True

        self.invincible = False

    def update(self, key_lst, screen: pg.Surface):
        """
        押下キーに応じてハートを移動させる
		引数1 moving_left：左移動フラグ
		引数2 moving_right：右移動フラグ
        引数3 screen：画面Surface
		"""
		# 移動量をリセット。dx,dyと表記しているのは微小な移動量を表すため。微分、積分で使うdx,dy。
        dx = 0
        dy = 0

		# 左に移動
        if key_lst[pg.K_LEFT]:
			# スピードの分だけ移動。座標系において左は負の方向
            dx = -self.speed

		# 右に移動
        if key_lst[pg.K_RIGHT]:
			# スピードの分だけ移動。座標系において左は負の方向
            dx = self.speed

        if key_lst[pg.K_UP] and self.in_air == False:
            # Y軸方向の速度
            self.vel_y = -11
			# 空中フラグを更新
            self.in_air = True
            
		# 重力を適用。Y軸方向の速度に重力を加える。この重力は重力速度である。単位時間あたりの速度と考えるので力をそのまま速度に足して良い。
        self.vel_y += GRAVITY
		# Y軸方向の速度が一定以上なら
        if self.vel_y > 10:
			# 速さはゼロになる
            self.vel_y
		# Y軸方向の微小な移動距離を更新.単位時間なので距離に速度を足すことができる
        dy += self.vel_y

        self.rect.move_ip([dx, dy])

        # 床との衝突判定
        if self.rect.bottom + dy > (HEIGHT/2-50)+300-5:
            dy = (HEIGHT/2-50)+300-5 - self.rect.bottom
			# 空中フラグを更新
            self.in_air = False
            self.rect.move_ip([0, dy])
        
        # 壁との衝突判定
        if self.rect.left < WIDTH/2-150+5 or WIDTH/2+150-5 < self.rect.right:  # 横判定
            dx = -dx
            self.rect.move_ip([dx, 0])

        if self.invincible:  # 無敵時間の設定
            if self.invincible_time == 0:
                self.invincible = False
                self.invincible_time = __class__.invincible_time
            else:
                self.invincible_time -= 1
                if self.invincible_time % 5 == 0:
                    screen.blit(self.image, self.rect)
        else:
            screen.blit(self.image, self.rect)


class HealthBar:
    """
    体力ゲージに関するクラス
    """
    def __init__(self, x: int, y: int, width: int, max: int, gpa: float):
        """
        引数1 x：表示するx座標
        引数2 y：表示するy座標
        引数3 width：体力ゲージの幅
        引数4 max：体力の最大値
        引数5 gpa：表示するgpaの値
        """
        self.x = x
        self.y = y
        self.width = width
        self.max = max # 最大HP
        self.hp = max # HP
        self.mark = int((self.width - 4) / self.max) # HPバーの1目盛り

        self.font = pg.font.Font(FONT_F, 28)
        # HPとgpa表示の設定
        self.label = self.font.render(f"GPA:{gpa:.1f}  HP ", True, (255, 255, 255))
        # 体力ゲージのバー表示の設定
        self.frame = Rect(self.x + 2 + self.label.get_width(), self.y, self.width, self.label.get_height())
        self.bar = Rect(self.x + 4 + self.label.get_width(), self.y + 2, self.width - 4, self.label.get_height() - 4)
        self.value = Rect(self.x + 4 + self.label.get_width(), self.y + 2, self.width - 4, self.label.get_height() - 4)

    def update(self):
        """
        体力の更新
        """
        self.value.width = self.hp * self.mark

    def draw(self, screen: pg.Surface):
        """
        残り体力の描画
        引数1 screen：画面サーファイス
        """
        pg.draw.rect(screen, (255, 0, 0), self.bar)
        pg.draw.rect(screen, (255, 255, 0), self.value)
        screen.blit(self.label, (self.x, self.y))
        # 現在のHPと最大HPの表示
        hp_text = self.font.render(f" {self.hp}/{self.max}", True, (255, 255, 255))
        screen.blit(hp_text, (self.x + self.width + 10 + self.label.get_width(), self.y))


class EnemyHealthBar:
    """
    敵の体力に関するクラス
    """
    def __init__(self, x: int, y: int, width: int, max: int):
        """
        引数1 x：表示するx座標
        引数2 y：表示するy座標
        引数3 width：体力ゲージの幅
        引数4 max：体力の最大値
        """
        # super().__init__()
        self.width = width//20+4
        self.x = x - self.width/2
        self.y = y
        self.max = max//20 # 最大HP
        self.hp = max # HP
        self.mark = int((self.width - 4) / self.max) # HPバーの1目盛り
        
        self.font1 = pg.font.Font(FONT_F, 40)
        # 体力ゲージのバー表示の設定
        self.frame = Rect(self.x , self.y, self.width, 31)
        self.bar = Rect(self.x, self.y + 2, self.width - 4, 31 - 4)
        self.value = Rect(self.x, self.y + 2, self.width - 4, 31 - 4)

    def update(self):
        """
        HPに対応したヘルスバーの更新
        """
        self.value.width = (self.hp//20) * self.mark

    def draw(self, screen: pg.Surface, dmg: int):
        """
        ヘルスバーとダメージの表示
        引数1 screen：画面Surface
        引数2 dmg：ダメージ量
        """
        pg.draw.rect(screen, (0, 0, 0), self.frame)
        pg.draw.rect(screen, (100, 100, 100), self.bar)
        pg.draw.rect(screen, (0, 255, 0), self.value)
        label1 = self.font1.render(f"{dmg}", True, (0, 0, 0), (255, 0, 0))
        rect1 = label1.get_rect()
        rect1.center = WIDTH/2-50, self.y - 50
        screen.blit(label1, rect1.center)


class Dialogue:
    """
    選択画面時のセリフに関するクラス
    """
    def __init__(self) -> None:
        """
        引数なし
        """
        self.font = pg.font.Font(FONT, 35)
        self.txt = "＊ こうかとんがあらわれた！"
        self.txt_len = len(self.txt)
        self.index = 0

    def update(self, screen: pg.Surface,reset=None):
        """
        引数1 screen：画面Surface
        引数2 reset：画面切り替え時に戻す
        """
        if self.index < self.txt_len:
            self.index += 1
        if reset:
            self.index = 0
        rend_txt = self.font.render(self.txt[:self.index], True, (255, 255, 255))
        screen.blit(rend_txt, (40, HEIGHT/2-20))


class Choice:
    """
    選択肢に関するクラス
    """
    def __init__(self, ls: list[str], x: int, y: int):
        """
        引数1 ls：表示する選択肢のリスト
        引数2 x：表示するx座標
        引数3 y：表示するy座標
        """
        self.choice_ls = ls
        self.x = x
        self.y = y
        
        self.font = pg.font.Font(FONT_F, 40)
        self.index = 0  # 選択しているものの識別用 

        self.whle = 50  # 四角形との間の距離 
        self.width = (WIDTH - (self.whle*(len(ls)-1)) - 20)/len(ls)
        self.height = 70

        self.switch_voice = pg.mixer.Sound("./voice/switch_select.wav")
        
    def draw(self, screen: pg.Surface, atk = False):
        """
        選択肢を表示する
        引数1 screen：画面Surface
        """
        for i, choice in enumerate(self.choice_ls):
            rect = pg.Rect(
                self.x + (self.width + self.whle) * i, # 四角形を描く開始座標
                self.y, 
                self.width, 
                self.height
                )
            if atk:
                color = (248, 138, 52)
            elif i == self.index:
                color = (255, 255, 0)
            else:
                color = (248, 138, 52)
            pg.draw.rect(screen, color, Rect(rect), 5)
            txt = self.font.render(choice, True, color)
            txt_rect = txt.get_rect()
            txt_rect.center = rect.center
            screen.blit(txt, txt_rect)

    def update(self, key):
        """
        キー入力による選択肢の変更
        引数1 key：押されたキーの識別
        """
        if key == pg.K_LEFT:
            self.index = (self.index - 1) % len(self.choice_ls)  # 右端から左端へ
            self.switch_voice.play(0)
        elif key == pg.K_RIGHT:
            self.index = (self.index + 1) % len(self.choice_ls)  # 左端から右端へ
            self.switch_voice.play(0)
            
        
class AfterChoice:
    """
    選択肢を選んだあとの画面に関するクラス
    """
    def __init__(self, lst: list[str]):
        """
        引数1 lst：選択肢のリスト
        """
        self.font = pg.font.Font(FONT, 35)
        self.txt_lst = lst
        self.index = 0  # 選択しているものの識別用 

        self.switch_voice = pg.mixer.Sound("./voice/switch_select.wav")

    def draw(self, screen: pg.Surface, action=False):
        x = 40
        y = HEIGHT/2-20
        for i, choice in enumerate(self.txt_lst):
            if action:
                color = (255, 255, 255)
            else:
                if i == self.index:
                    color = (255, 255, 0)
                else:
                    color = (255, 255, 255)
            rend_txt = self.font.render(choice, True, color)
            screen.blit(rend_txt, (x, y))
            if action:  # こうどうを選択したときのみ、こちらでyのみを増やす
                y += 60
            else:
                if i % 2 == 0:
                    x = WIDTH/2 + 40
                else:
                    x = 40
                    y += 60

    def update(self, key):
        """
        # キー入力による選択肢の変更
        # 引数1 key：押されたキーの識別
        """
        if key == pg.K_LEFT:
            self.index = (self.index - 1) % len(self.txt_lst)  # 右端から左端へ
            self.switch_voice.play(0)
        elif key == pg.K_RIGHT:
            self.index = (self.index + 1) % len(self.txt_lst)  # 左端から右端へ
            # print(self.index)
            self.switch_voice.play(0)


class AttackBar:
    """
    敵を攻撃するアタックバーに関する関数
    """
    img = pg.transform.rotozoom(
        pg.image.load("fig/Attack_Bar.png"),
        0,1.8
    )
    def __init__(self, screen_width, screen_height):
        """
        アタックバーの初期化
        引数1 screen_width：行動範囲の横サイズ
        引数2 screen_height：行動範囲の縦サイズ
        """
        # アタックの確率バーの描画
        self.rect = pygame.Rect(15, HEIGHT/2-45, 20, 290)
        self.speed = 35 # 35 # 70
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.moving_right = True
        self.moving = True

        # アタックバーの描画
        self.img = __class__.img
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = WIDTH/2, HEIGHT/2+100

    def move(self):
        """
        アタックバーの移動について
        """
        if self.moving:
            if self.moving_right:
                self.rect.x += self.speed
            else:
                self.rect.x -= self.speed

        yoko, tate = check_bound(self.rect, 15, self.screen_width, 0, self.screen_height)
        if not yoko:
                self.moving_right = not self.moving_right

    def draw(self, screen: pg.Surface):
        """
        アタックバーを描画する
        """
        screen.blit(self.img, self.rct)
        pg.draw.rect(screen, (255, 255, 255), self.rect)

    def stop(self):
        """
        アタックバーを止める
        """
        self.moving = not self.moving


class GameOver:
    """
    ゲームオーバー画面に関するクラス
    """
    def __init__(self, rand : int):
        self.font = pg.font.Font(FONT_F, 150)
        self.txt1 = "GAME"
        self.txt2 = "OVER"
        self.txt_mes = [
            "あきらめては　いけない...", 
            "あきらめては　ダメだ！",
            "たんいを　すてるな！",
            "しっかりしろ！",
            ]
        self.font2 = pg.font.Font(FONT, 50)
        self.txt3 = self.txt_mes[rand]
        self.txt_len = len(self.txt3)
        self.index = 0
        self.tmr = 0

    def update(self, screen: pg.Surface,reset=None):
        """
        引数1 screen：画面Surface
        引数2 reset：画面切り替え時に戻す
        """
        rend_txt1 = self.font.render(self.txt1, False, (255, 255, 255))
        txt_rect1  = rend_txt1.get_rect()
        txt_rect1.center = WIDTH/2, 2*HEIGHT/6
        screen.blit(rend_txt1, txt_rect1)
        rend_txt2 = self.font.render(self.txt2, False, (255, 255, 255))
        txt_rect2  = rend_txt2.get_rect()
        txt_rect2.center = WIDTH/2, 3*HEIGHT/6
        screen.blit(rend_txt2, txt_rect2)

        if reset:
            self.index = 0
            self.tmr = 0
        if self.tmr > 30:
            if self.index < self.txt_len:
                self.index += 1
            rend_txt3 = self.font2.render(self.txt3[:self.index], True, (255, 255, 255))
            txt_rect3  = rend_txt3.get_rect()
            txt_rect3.center = WIDTH/2, 4*HEIGHT/6
            screen.blit(rend_txt3, txt_rect3)
        self.tmr += 1


class BreakHeart:
    """
    ゲームオーバー時にハートを壊すことに関するクラス
    """
    himg = pg.transform.rotozoom(
        pg.image.load("fig/Undertale_hurt.png"), 
        0, 0.02
        ) 
    bimg = pg.transform.rotozoom(
        pg.image.load("fig/Undertale_breakhurt.png"), 
        0, 0.02
        ) 
    def __init__(self, x:int, y:int):
        """
        引数1 x：ハートの最終座標x
        引数2 y：ハートの最終座標y
        """
        self.himg = __class__.himg
        self.bimg = __class__.bimg
        self.rect1: pg.Rect = self.himg.get_rect()
        self.rect2: pg.Rect = self.bimg.get_rect()
        self.rect1.center = (x, y)
        self.rect2.center = (x, y)

        self.break_heart = pg.mixer.Sound("./voice/break_heart.wav")

        self.tmr = 0
    
    def update(self, screen: pg.Surface, reset=False):
        """
        引数1 screnn：画面Surface
        引数2 reset：れセット判定
        """
        if reset:
            self.tmr = 0
        if self.tmr < 20:
            screen.blit(self.himg, self.rect1)
        elif 20 == self.tmr:
            self.break_heart.play(0)
        elif 20 < self.tmr:
            screen.blit(self.bimg, self.rect2)
        self.tmr += 1


class GameTitle:
    """
    ゲームタイトルを表示するためのクラス
    """
    img = pg.transform.rotozoom(
        pg.image.load("fig/KoukAtale_Title.png"), 
        0, 1
        ) 
    def __init__(self):
        """
        引数なし
        """
        # タイトル画像
        self.img = __class__.img
        self.rect = self.img.get_rect()
        self.rect.center = WIDTH/2, HEIGHT/2
        # 文字
        self.font = pg.font.Font(FONT, 40)
        self.font1 = pg.font.Font(FONT, 50)
        self.txt = self.font.render("Please press the Enter Key", True, (255, 255, 255))
        self.txt_rect = self.txt.get_rect()
        self.txt_rect.center = WIDTH/2, 2*HEIGHT/3
        self.explan = "---操作説明---\n\n[ENTER]-決定\n[ESC]-戻る\n[方向キー]-移動\n\nHPが0になったらあなたのまけ。"
        self.ex_rect = pg.Rect(WIDTH/8, HEIGHT/8, 760, 560)
        self.line_space = 40
        # サウンド
        self.titlenoise = pg.mixer.Sound("./voice/intronoise.wav")
        self.menu = pg.mixer.Sound("./sound/menu1.mp3")
        # タイマー
        self.tmr = 0
        # フラグ
        self.end_title = 0

    def update(self, screen: pg.Surface):
        """
        引数1 screen：画面Surface
        """
        screen.blit(self.img, self.rect)
        y = self.ex_rect.top
        if self.end_title == 0 or self.end_title == 1:
            if self.tmr == 0:
                self.titlenoise.play(0)
            elif self.tmr > 50:
                screen.blit(self.txt, self.txt_rect)
                self.end_title = 1
        elif self.end_title == 2 or self.end_title == 3:
            if self.tmr == 0:
                self.menu.play(-1)
            elif self.tmr > 1:
                screen.fill((0,0,0))
                for line in self.explan.splitlines():
                    image = self.font1.render(line, False, (255, 255, 255))
                    screen.blit(image, (self.ex_rect.left, y))
                    y += self.font.size(line)[1] + self.line_space
                self.end_title = 3
        self.tmr += 1


class GameEndVerAtk:
    """
    こうかとんを倒したときに関するクラス
    """
    img1 = pg.transform.rotozoom(
        pg.image.load("fig/dot_kb1.png"), 
        0, 1.5
        )
    img2 = pg.transform.rotozoom(
        pg.image.load("fig/dot_kb2.png"), 
        0, 1.5
        )
    img3 = pg.transform.rotozoom(
        pg.image.load("fig/dot_kk_negate_end.png"), 
        0, 1.5
        )
    x = WIDTH/2
    y = HEIGHT/4+30

    def __init__(self, kkton: 'Koukaton'):
        """
        引数1 kkton：こうかとんクラス
        """
        self.x = __class__.x
        self.y = __class__.y
        self.img_cry = __class__.img1  # 泣き顔
        self.rect_cry: pg.Rect = self.img_cry.get_rect()
        self.rect_cry.center = self.x, self.y

        self.img_sup = __class__.img2  # 驚き顔
        self.rect_sup: pg.Rect = self.img_sup.get_rect()
        self.rect_sup.center = self.x, self.y

        self.img_sup2 = __class__.img3  # kkotn驚き顔
        self.rect_sup2: pg.Rect = self.img_sup2.get_rect()
        self.rect_sup2.center = self.x, self.y
        
        self.tmr = 0
        
        self.talk = Talk(kkton)

        self.wave_amp = 0  # 波の振幅
        self.wave_freq = 0  # 波の周波数
        self.wave_speed = 0  # 波の速さ

        self.gameend = False  # 終了ムービーが終わったか

    def update(self, screen:pg.Surface):
        """
        引数1 screen：画面Surface
        以下はこうかとんが倒されたときの会話を描画する
        """
        if 0 <= self.tmr <= 20:
            if self.tmr % 2 == 0:
                self.rect_sup2.centerx = self.x + 20
            else:
                self.rect_sup2.centerx = self.x - 20
            screen.blit(self.img_sup2, self.rect_sup2)
        elif 20 < self.tmr < 40:
            self.rect_sup2.centerx = self.x
            screen.blit(self.img_sup2, self.rect_sup2)
        elif 40 <= self.tmr < 80:
            screen.blit(self.img_sup2, self.rect_sup2)
            lines = "..."
            self.talk.update(screen,lines,len(lines), self.tmr)
        elif 80 == self.tmr:
            self.talk.index = 0
            screen.blit(self.img_sup2, self.rect_sup2)
        elif 80 < self.tmr < 120:
            self.rect_sup2.centerx = self.x
            screen.blit(self.img_sup2, self.rect_sup2)
            lines = "..."
            self.talk.update(screen,lines,len(lines), self.tmr)
        elif 120 == self.tmr:
            self.talk.index = 0
            screen.blit(self.img_sup2, self.rect_sup2)
        elif 120 < self.tmr < 200:
            self.rect_sup2.centerx = self.x
            screen.blit(self.img_sup2, self.rect_sup2)
            lines = "どうやらここまでみたいだ..."
            self.talk.update(screen,lines,len(lines), self.tmr)
        elif 200 <= self.tmr < 240:
            for y in range(self.rect_sup2.height):
                self.wave_amp += 0.01
                self.wave_freq += 0.1
                self.wave_speed += 0.0001
                offset = int(self.wave_amp * math.sin(self.wave_freq * (y + pg.time.get_ticks() * self.wave_speed)))  # サイン波の形成
                screen.blit(self.img_sup2, 
                            (offset+__class__.x-self.rect_sup2.width/2, y+__class__.y-self.rect_sup2.height/2), 
                            (0, y, self.rect_sup2.width, 1)
                            )
        elif 240 <= self.tmr < 280:
            for y in range(self.rect_sup.height):
                self.wave_amp -= 0.01
                self.wave_freq -= 0.1
                self.wave_speed -= 0.0001
                offset = int(self.wave_amp * math.sin(self.wave_freq * (y + pg.time.get_ticks() * self.wave_speed)))  # サイン波の形成
                screen.blit(self.img_sup, 
                            (offset+__class__.x-self.rect_sup.width/2, y+__class__.y-self.rect_sup.height/2), 
                            (0, y, self.rect_sup.width, 1)
                            )
        elif 280 <= self.tmr < 320:
            screen.blit(self.img_sup, self.rect_sup)
        elif self.tmr == 320:
            self.talk.index = 0
            screen.blit(self.img_sup, self.rect_sup)
        elif 320 <= self.tmr < 400:
            lines = "だましてごめんよ"
            self.talk.update(screen,lines,len(lines), self.tmr)
            screen.blit(self.img_cry, self.rect_cry)
        elif self.tmr == 400:
            self.talk.index = 0
            screen.blit(self.img_cry, self.rect_cry)
        else:
            screen.blit(self.img_cry, self.rect_cry)
            self.rect_cry.x -= 10
            if self.rect_cry.right < 0:
                self.gameend = True

        self.tmr += 1


class Talk:
    """
    会話に関するクラス
    """
    img = pg.transform.rotozoom(
        pg.image.load("fig/Speech_bubble.png"), 
        0, 0.3
        )
    # x = 4*WIDTH/7
    y = HEIGHT/6

    def __init__(self, kkton:'Koukaton'):
        """
        引数1 kkton：こうかとんクラス
        """
        self.kkton = kkton

        # ふきだしの設定
        self.img = __class__.img
        self.rect = self.img.get_rect()
        self.rect.y = Talk.y
        # self.max_width = self.rect.width - 20  # 吹き出し内の最大幅

        self.font = pg.font.Font(FONT, 20)
        self.index = 0

        self.voice = pg.mixer.Sound("./voice/sanzu_voice.wav")

    def update(self, screen: pg.Surface, lines: str, len:int, tmr:int):
        """
        セリフを表示する
        引数1 screen：画面Surface
        引数2 lines：表示させたいセリフの文字列
        引数3 len：文字列の長さ
        引数4 tmr：表示しているときのタイマー
        """
        self.rect.x = self.kkton.rect.right
        screen.blit(self.img, self.rect)
        if self.index < len:
            if tmr % 2 == 0:
                self.index += 1
                self.voice.play(0)

        lines_list = lines[:self.index].split('\n')
        y_offset = 0

        for line in lines_list:
            line_txt = self.font.render(line, True, (0, 0, 0))
            screen.blit(line_txt, (self.kkton.rect.right + 80, __class__.y + 30 + y_offset))
            y_offset += line_txt.get_height()  # 次の行のY座標を計算


class Item:
    """
    アイテムの処理に関するクラス
    """
    def __init__(self):
        self.dic = {
            "＊　こうかとんエキス":15, 
            "＊　こうかとんジュース":15, 
            "＊　こうかとんエナジー":25, 
            "＊　こうかとんドリンク":30,
        }
        self.cure_voice = pg.mixer.Sound("./voice/cure.wav")
        self.next = False

    def cure(self, hp:"HealthBar", item: str, lst: list):
        """
        引数1 hp：HPの残り残量
        引数2 item：なんのアイテムを使用したか
        引数3 lst：残りの使えるアイテムのリスト
        アイテムに応じた体力の回復を行う
        """
        if hp.max > hp.hp:
            self.cure_voice.play(0)
            hp.hp += self.dic[item]
            if hp.hp > hp.max:
                hp.hp = hp.max
            lst.remove(item)
            self.next = True
        else:
            self.next = False


"""
以下にこうかとんが攻撃する内容についてのクラスを用意する
"""
class AttackRakutan(pg.sprite.Sprite):
    """
    こうかとんの落単ビーム攻撃に関するクラス
    これは例です。
    """
    def __init__(self, color: tuple[int, int, int],start_pos: tuple[int, int]):
        """
        引数に基づき攻撃Surfaceを生成する
        引数1 color：色指定
        引数2 start_pos：スタート位置
        """
        super().__init__()
        self.vx, self.vy = 0, +10

        self.font = pygame.font.Font(FONT, 18)
        self.label = self.font.render("落単", False, (50, 50, 50))
        self.frct = self.label.get_rect()
        self.frct.center = start_pos

        self.image = pg.Surface((100, 20))
        pg.draw.rect(self.image, color, (0, 0, 100, 20))
        self.rect = self.image.get_rect()
        self.rect.center = start_pos        

    def update(self, screen: pg.Surface, reset=False):
        """
        引数1 screen：画面Surface
        引数2 reset：リセット判定
        """
        self.rect.move_ip(self.vx, self.vy)
        screen.blit(self.image, self.rect)
        self.frct.move_ip(self.vx, self.vy)
        screen.blit(self.label, self.frct)
        if check_bound1(self.rect) != (True, True) or reset:
            self.kill()  
"""
うえの例をもとに以下にこうかとんが攻撃する内容についてのクラスを各自用意する
"""
class DreamEgg(pg.sprite.Sprite):
    """
    こうかとんの卵攻撃に関するクラス
    """
    def __init__(self, kkton: "Koukaton", heart: "Heart", angle = 0):
        """
        卵の初期化
        引数1 kkton：こうかとんクラス
        引数2 heart：ハートクラス
        引数3 angle：ハートへのアングル
        """
        super().__init__()
        # 卵（円）の設定
        rad = 10
        self.image = pg.Surface((2*rad, 2*rad))
        color = (255, 255, 255)
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()

        # 座標の設定
        self.rect.centerx = kkton.rect.centerx-40 # バッグから出ているように調整
        self.rect.centery = kkton.rect.centery+kkton.rect.height//2-40
        
        # 場所と向きの設定
        kkton.rect.x = random.randint(WIDTH/2-50, WIDTH/2+50)
        self.vx, self.vy = calc_orientation(kkton.rect, heart.rect)
        angle = math.degrees(math.atan2(-self.vy, self.vx)) + angle
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        
        self.speed = 10

    def update(self, screen: pg.Surface, reset=False):
        """
        DreamEggの描画
        引数1 screen：画面Surface
        引数2 reset：リセット用
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        screen.blit(self.image, self.rect)
        if check_bound1(self.rect) != (True, True) or reset:
            self.kill()


class FollowingBeam(pg.sprite.Sprite):
    """
    追従するビームに関するクラス
    """
    def __init__(self, heart: "Heart", start_pos: tuple[int, int], angle = 0, follow = False):
        """
        ビームの初期化
        引数1 heart：ハートクラス
        引数2 angle：ハートへのアングル
        引数3 follow：ハートに追従するか
        """
        super().__init__()

        # ビームの四角形を描画
        self.image = pg.Surface((100, 30))
        pg.draw.rect(self.image, (255, 255, 255), (0, 0, 100, 30))
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = start_pos

        if follow:  # 追従する場合
            self.vx, self.vy = calc_orientation(self.rect, heart.rect)
        else:  # 中心座標の場合
            self.img = pg.Surface((0,0))
            self.irect = self.img.get_rect()
            self.irect.center = WIDTH/2, HEIGHT/2+100

            self.vx, self.vy = calc_orientation(self.rect, self.irect)
        
        # 向きと設定
        angle = math.degrees(math.atan2(-self.vy, self.vx)) + angle
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))

        # イメージの向きの設定
        self.image = pg.transform.rotate(self.image, angle)

        # 時間
        self.tmr = 0
    
    def update(self, screen: pg.Surface, reset=False):
        """
        DreamEggの描画
        引数1 screen：画面Surface
        引数2 reset：リセット用
        """
        screen.blit(self.image, self.rect)
        if self.tmr > 10:
            self.rect.move_ip(20*self.vx, 20*self.vy)
        
        if self.tmr > 50 or reset:
            self.kill()
        self.tmr += 1


class Minefield(pg.sprite.Sprite):
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)

    def __init__(self, screen):
        super().__init__()
        self.screen = screen
        self.bombs = pg.sprite.Group()

    def place_bombs(self):
        self.bombs.empty()
        num_bombs = random.randint(5, 8)
        for _ in range(num_bombs):
            x = random.randint(int(WIDTH / 2 - 150 + 5), int(WIDTH / 2 + 150 - 5))
            y = random.randint(int(HEIGHT / 2 - 50 + 5), int(HEIGHT / 2 - 50 + 300 - 5))
            bomb = pg.sprite.Sprite()
            bomb.rect = pg.Rect(x, y, 10, 10)
            self.bombs.add(bomb)

    def draw(self):
        for bomb in self.bombs:
            pg.draw.rect(self.screen, self.WHITE, bomb.rect)


class Explosion(pg.sprite.Sprite):
    EXPLOSION_COLOR = (194, 0, 0)

    def __init__(self, screen):
        super().__init__()
        self.screen = screen
        self.explosions = pg.sprite.Group()

    def create_explosions(self, bombs):
        self.explosions.empty()
        for bomb in bombs:
            explosion = pg.sprite.Sprite()
            explosion.rect = pg.Rect(bomb.rect.centerx - 30, bomb.rect.centery - 30, 60, 60)
            self.explosions.add(explosion)

    def draw(self):
        for explosion in self.explosions:
            pg.draw.circle(self.screen, self.EXPLOSION_COLOR, explosion.rect.center, 30)


class SideBeamFake(pg.sprite.Sprite):
    """
    予告ビームが出てくるクラス
    """
    def __init__(self, start_pos: tuple[int, int]):
        """
        予告ビームの初期化
        start_pos：スタート位置
        """
        super().__init__()

        self.image = pg.Surface((300, 100), pg.SRCALPHA)
        pg.draw.rect(self.image, (255, 255, 0), (0, 0, 300, 100))
        self.image.fill((255, 255, 0, 100))
        self.rect = self.image.get_rect()
        self.rect.center = start_pos

        self.tmr = 0
        self.sidebeam_voice = pg.mixer.Sound("./voice/sanzu_beam2.wav")
        self.sidebeam_voice.play(0)

    def update(self, screen, reset=False):
        """
        mainのattack_tmrが0~20, 40~60, 80~100,,,の間、予告ビームを表示する
        """
        self.tmr += 1
        screen.blit(self.image, self.rect)
        if self.tmr == 20 or reset:
            self.kill() 


class SideWallReal(pg.sprite.Sprite):
    """
    横からビームが出てくるクラス
    """
    def __init__(self, start_pos: tuple[int, int]):
        """
        横からビームの初期化
        start_pos：スタート位置
        """
        super().__init__()
        self.genx = 0
        self.geny = 0
        self.gengeny = 100
        self.pos = start_pos

        self.image = pg.Surface((300, 100), pg.SRCALPHA)
        pg.draw.rect(self.image, (255, 255, 255), (self.genx, self.geny, 300, self.gengeny))
        self.rect = self.image.get_rect()
        self.rect.center = start_pos

        self.tmr = 0

    def update(self, screen, reset=False):
        """
        mainのattack_tmrが40~60, 80~100,,,の間、表示できるようにする
        """
        self.tmr += 1
        self.gengeny -= 3.0
        self.geny += 1.5
        if 1 <= self.tmr < 21:
            self.image = pg.Surface((300, 100), pg.SRCALPHA)
            pg.draw.rect(self.image, (255, 255, 255), (self.genx, self.geny, 300, self.gengeny))
            self.rect = self.image.get_rect()
            self.rect.center = self.pos
            screen.blit(self.image, self.rect)
        if self.tmr == 21 or reset:
            self.kill() 


class SideBeamFake(pg.sprite.Sprite):
    """
    予告ビームが出てくるクラス
    """
    def __init__(self, start_pos: tuple[int, int]):
        """
        予告ビームの初期化
        start_pos：スタート位置
        """
        super().__init__()

        self.image = pg.Surface((300, 100), pg.SRCALPHA)
        pg.draw.rect(self.image, (255, 255, 0), (0, 0, 300, 100))
        self.image.fill((255, 255, 0, 100))
        self.rect = self.image.get_rect()
        self.rect.center = start_pos

        self.tmr = 0
        self.sidebeam_voice = pg.mixer.Sound("./voice/sanzu_beam2.wav")
        self.sidebeam_voice.play(0)

    def update(self, screen, reset=False):
        """
        mainのattack_tmrが0~20, 40~60, 80~100,,,の間、予告ビームを表示する
        """
        self.tmr += 1
        screen.blit(self.image, self.rect)
        if self.tmr == 20 or reset:
            self.kill() 


class SideWallReal(pg.sprite.Sprite):
    """
    横からビームが出てくるクラス
    """
    def __init__(self, start_pos: tuple[int, int]):
        """
        横からビームの初期化
        start_pos：スタート位置
        """
        super().__init__()
        self.genx = 0
        self.geny = 0
        self.gengeny = 100
        self.pos = start_pos

        self.image = pg.Surface((300, 100), pg.SRCALPHA)
        pg.draw.rect(self.image, (255, 255, 255), (self.genx, self.geny, 300, self.gengeny))
        self.rect = self.image.get_rect()
        self.rect.center = start_pos

        self.tmr = 0

    def update(self, screen, reset=False):
        """
        mainのattack_tmrが40~60, 80~100,,,の間、表示できるようにする
        """
        self.tmr += 1
        self.gengeny -= 3.0
        self.geny += 1.5
        if 1 <= self.tmr < 21:
            self.image = pg.Surface((300, 100), pg.SRCALPHA)
            pg.draw.rect(self.image, (255, 255, 255), (self.genx, self.geny, 300, self.gengeny))
            self.rect = self.image.get_rect()
            self.rect.center = self.pos
            screen.blit(self.image, self.rect)
        if self.tmr == 21 or reset:
            self.kill() 


class Bound_Beam(pg.sprite.Sprite):
    def __init__(self,color: tuple[int, int, int], start_pos: tuple[int, int]):  # コンストラクタ。開始位置と半径を引数に取ります。
        """
        引数に基づきボールSurfaceを生成する
        start_pos：スタート位置
        radius：ボールの半径
        """
        super().__init__()  # 親クラスのコンストラクタを呼び出します。
        self.vx = random.uniform(-7, 7)  # x方向の速度をランダムに設定
        self.vy = random.uniform(-7, 7)  # y方向の速度をランダムに設定
        self.radius = 10
        self.image = pg.Surface((self.radius * 2, self.radius * 2),pg.SRCALPHA)
        pg.draw.circle(self.image, color, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect()
        self.rect.center = start_pos

    def update(self, screen: pg.Surface,reset=False):  # updateメソッド。画面Surfaceを引数に取ります。
        """
        引数1 screen：画面Surface
        """
        self.rect.move_ip(self.vx, self.vy)

        # 画面の端に当たった場合、速度の方向を反転させます。
        self.rect.move_ip(self.vx, self.vy)
        screen.blit(self.image, self.rect)
        bound_x, bound_y = check_bound2(self.rect)
        if not bound_x:
            self.vx = -self.vx
        if not bound_y:
            self.vy = -self.vy
        if reset:
            self.kill()


class Bound_Beam(pg.sprite.Sprite):
    def __init__(self,color: tuple[int, int, int], start_pos: tuple[int, int]):  # コンストラクタ。開始位置と半径を引数に取ります。
        """
        引数に基づきボールSurfaceを生成する
        start_pos：スタート位置
        radius：ボールの半径
        """
        super().__init__()  # 親クラスのコンストラクタを呼び出します。
        self.vx = random.uniform(-7, 7)  # x方向の速度をランダムに設定
        self.vy = random.uniform(-7, 7)  # y方向の速度をランダムに設定
        self.radius = 10
        self.image = pg.Surface((self.radius * 2, self.radius * 2),pg.SRCALPHA)
        pg.draw.circle(self.image, color, (self.radius, self.radius), self.radius)
        self.rect = self.image.get_rect()
        self.rect.center = start_pos

    def update(self, screen: pg.Surface,reset=False):  # updateメソッド。画面Surfaceを引数に取ります。
        """
        引数1 screen：画面Surface
        """
        self.rect.move_ip(self.vx, self.vy)

        # 画面の端に当たった場合、速度の方向を反転させます。
        self.rect.move_ip(self.vx, self.vy)
        screen.blit(self.image, self.rect)
        bound_x, bound_y = check_bound2(self.rect)
        if not bound_x:
            self.vx = -self.vx
        if not bound_y:
            self.vy = -self.vy
        if reset:
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    上下左右からビームを出す攻撃クラス
    """
    def __init__(self, color: tuple[int, int, int],start_pos: tuple[int, int], speed: tuple[int, int], tate=False):
        """
        引数に基づき攻撃Surfaceを生成する
        color：色
        start_pos：スタート位置
        """
        super().__init__()
        self.vx, self.vy = speed

        self.image = pg.Surface((100, 20), pg.SRCALPHA)
        pg.draw.rect(self.image, color, (0, 0, 100, 20))
        if tate:
            self.image = pg.transform.rotozoom(
                self.image, 
                90,
                1
            )
        self.rect = self.image.get_rect()
        self.rect.x = start_pos[0]
        self.rect.y = start_pos[1]        

    def update(self, screen: pg.Surface, reset=False):
        """
        引数1 screen：画面Surface
        """
        self.rect.move_ip(self.vx, self.vy)
        screen.blit(self.image, self.rect)
        if check_bound1(self.rect) != (True, True) or reset:
            self.kill()  
    

def main():
    pg.display.set_caption("koukAtale")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    """
    ゲームのシーンを切り替えるための変数(Flag)
    """
    scenechange = 0  # 0: タイトル, 1:ゲームプレイ, 2:ゲームオーバー , 3:ゲームクリア
    gameschange = 0  # 0：選択画面, 1：攻撃相手選択
    """
    以下クラスの初期化
    """
    kkton = Koukaton()
    heart = Heart((WIDTH/2, HEIGHT/2+100 ))
    # heart = HeartGrav((WIDTH/2, HEIGHT/2+100))
    dialog = Dialogue()
    gpa = random.uniform(2, 4)
    max_hp = int(gpa*20)
    hp = HealthBar(WIDTH/4, 5*HEIGHT/6, max_hp+4, max_hp, gpa)
    en_max_hp = 7957
    en_hp = EnemyHealthBar(WIDTH/2, HEIGHT/3, en_max_hp, en_max_hp)
    choice_ls = ["たたかう", 
                 "こうどう", 
                 "アイテム", 
                 "みのがす"]
    choice = Choice(choice_ls, 10, HEIGHT - 80)
    choice_attack_lst = ["＊　こうかとん"]
    choice_attack = AfterChoice(choice_attack_lst) 
    choice_escape_ls = ["＊　にがす"]
    choice_escape = AfterChoice(choice_escape_ls)
    choice_action_lst = [
        "＊　こうかとんを分析", 
        "＊　こうかとんと話す", 
        "＊　こうかとんを焼く", 
        "＊　こうかとんを説得する",
        ]
    choice_action = (AfterChoice(choice_action_lst))
    choice_item_lst = [
        "＊　こうかとんエキス", 
        "＊　こうかとんジュース", 
        "＊　こうかとんエナジー", 
        "＊　こうかとんドリンク",
        ]
    choice_item = (AfterChoice(choice_item_lst))
    attack_bar = AttackBar(WIDTH-15, 300-(HEIGHT/2-50))
    gameov = GameOver(random.randint(0, 3))
    gameti = GameTitle()
    gameend_atk = GameEndVerAtk(kkton)
    item = Item()
    talk = Talk(kkton)

    # これ以下に攻撃のクラスを初期化する
    rakutan = pg.sprite.Group()
    dream_egg = pg.sprite.Group()
    follow_bream = pg.sprite.Group()
    minefield = Minefield(screen)
    explosion = Explosion(screen)
    sidebeamr = pg.sprite.Group()
    sidebeamf = pg.sprite.Group()
    beamw = pg.sprite.Group()
    beamh = pg.sprite.Group()    
    bound_beam = pg.sprite.Group()

    """
    以下それぞれのシーンのタイマーを用意
    もし用意したければここに追加してください
    """
    clock = pg.time.Clock()  # time
    select_tmr = 0  # 選択画面時のタイマーの初期値
    attack_tmr = 0  # 攻撃中のタイマーの初期値
    gameover_tmr = 0  # gameover中のタイマー
    """
    効果音やBGMの変数を用意
    """
    pg.mixer.init()
    select_voice = pg.mixer.Sound("./voice/snd_select.wav")
    attack_voice = pg.mixer.Sound("./voice/attack.wav")
    sound = pg.mixer.Sound("./sound/Megalovania.mp3")
    """
    その他必要な初期化
    """
    attack_num = 7  # 攻撃の種類に関する変数
    attack_rand = 0  # ランダムにこうかとんの攻撃を変えるための変数
    atk = False
    no_attack: bool = True  # 一度でも攻撃したかどうか
    no_attack_num = 0  # 何回攻撃されたか
    end_judg = 20  # 何回攻撃されたら見逃すかに関する変数
    restart = False # リスタート判定
    rand = 0

    # ゲーム開始
    while True:
        """
        scenechange変数の値に応じた画面を表示する
        """
        screen.fill((0,0,0))  # 背景を描画

        if scenechange == 0:  # タイトル画面
            """
            タイトル画面
            """
            # キー操作による状態遷移
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_RETURN:
                        if gameti.end_title == 1:
                            gameti.end_title = 2
                            gameti.tmr = 0
                        elif gameti.end_title ==3:
                            scenechange = 1
                            gameti.menu.stop()
                            sound.play(-1)

            gameti.update(screen)

        elif scenechange == 1:  # ゲームプレイ画面
            """
            ゲームプレイシーン
            gamechange変数に応じた画面を表示する
            """
            if gameschange == 0:  # 選択画面
                # キー操作による状態遷移
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return
                    elif event.type == pg.KEYDOWN:
                        choice.update(event.key)
                        if event.key == pg.K_RETURN:  # エンターキーを押されたら
                            if choice.index == 0:  # こうげきを選択していたら
                                select_voice.play(0)
                                gameschange = 1
                            elif choice.index == 1:  # こうどうを選択していたら
                                select_voice.play(0)
                                gameschange = 4
                            elif choice.index == 2 and len(choice_item_lst) != 0:  # アイテムを選択していたら
                                select_voice.play(0)
                                gameschange = 5
                            elif choice.index == 3:  # みのがすを選択していたら
                                select_voice.play(0)
                                gameschange = 10
                attack_rand = 4#random.randint(0, attack_num)
                attack_tmr = 0
                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)  # 大枠を描画
                kkton.update(screen)  # こうかとんを描画
                dialog.update(screen)  # 「こうかとんがあらわれた！」を表示
                hp.draw(screen)  # 残り体力を描画
                hp.update()  # 残り体力を更新
                choice.draw(screen)  # 選択肢の対か
            
            elif gameschange == 1:  # 「こうげき」を選択した場合
                # キー操作による状態遷移
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return
                    elif event.type == pg.KEYDOWN:
                        if event.key == pg.K_ESCAPE:
                            gameschange = 0
                        elif event.key == pg.K_RETURN:
                            select_voice.play(0)
                            gameschange = 2

                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)  # 大枠を描画
                choice_attack.draw(screen)  # 渡したリストを表示
                kkton.update(screen)  # こうかとんの表示
                hp.draw(screen)  # 残り体力の描画
                hp.update()  # 残り体力の更新
                choice.draw(screen)  # 選択肢の更新

            elif gameschange == 2:  # アタックバー画面
                # キー操作による状態遷移
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return
                    elif event.type == pg.KEYDOWN:
                        if event.key == pg.K_RETURN:
                                atk = True

                if en_hp.hp <= 0: # 敵の体力が0になったら
                    sound.stop()
                    scenechange = 3

                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)  # 大枠を描画
                kkton.update(screen)  # こうかとんの表示
                if atk:  # atkが有効かされたら 
                    no_attack = False
                    attack_bar.stop()  # バーを止める
                    if select_tmr == 0:
                        attack_voice.play(0)
                    if select_tmr == 3:
                        atk_value = 500 - int(abs((WIDTH/2-attack_bar.rect.centerx)/1.5))
                        en_hp.hp -= atk_value  # 敵の体力から減らす
                    elif 3 < select_tmr < 30:
                        en_hp.draw(screen, atk_value)
                        en_hp.update()
                    elif 30 < select_tmr:
                        atk = False
                        attack_bar.vx = +1
                        gameschange = 3
                    select_tmr += 1
                else:
                    attack_bar.move()  # バーを更新
                attack_bar.draw(screen)  # バーを描画
                hp.draw(screen)  # 残り体力の表示
                choice.draw(screen)  # 選択肢の表示

            elif gameschange == 3:  # 攻撃される画面
                # キー操作による状態遷移
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return
                """
                以下にこうかとんの攻撃画面が表示される。
                攻撃の描画やあたり判定などはここで行うこと
                """
                pg.draw.rect(screen,(255,255,255), Rect(WIDTH/2-150, HEIGHT/2-50, 300, 300), 5)
                if hp.hp <= 0:
                    """
                    hpが0になったらゲームオーバー画面へと変更するようにしている
                    """
                    sound.stop()
                    breakheart = BreakHeart(heart.rect.x, heart.rect.y)
                    scenechange = 2

                if no_attack and attack_tmr < 75:  # 平和end用
                    if no_attack_num == end_judg//2:
                        lines = "キミ、こうげきしてこないね"
                        talk.update(screen,lines,len(lines), attack_tmr)
                    elif no_attack_num == 2*end_judg//3:
                        lines = "もしかして\nこうげきしなかったら\n単位もらえると思ってる？"
                        talk.update(screen,lines,len(lines), attack_tmr)
                    elif no_attack_num == 4*end_judg//5:
                        lines = "ﾌﾌﾌ...\nキミ本当にやさしいね\nそろそろ僕もつかれてきたな"
                        talk.update(screen,lines,len(lines), attack_tmr)
                    elif no_attack_num == end_judg:
                        lines = "わかったよ\nキミの願いをかなえてあげるよ\nまた遊ぼうね"
                        talk.update(screen,lines,len(lines), attack_tmr)
                    elif no_attack_num > end_judg:
                        lines = "何してるんだい？\n遊べて楽しかったよ\n早くお逃げ"
                        talk.update(screen,lines,len(lines), attack_tmr)

                if attack_rand == 0:
                    """
                    以下は攻撃の描画を行う例である。
                    """
                    # 落単ビームの発生
                    if attack_tmr % 11 == 0:  # 一定時間ごとにビームを生成
                        start_pos = (random.randint(WIDTH/2-100,WIDTH/2+100), 40)
                        rakutan.add(AttackRakutan((255, 255, 255), start_pos))
                    # 落単との衝突判定
                    if len(pg.sprite.spritecollide(heart, rakutan, False)) != 0:
                        if heart.invincible == False:
                            if hp.hp < 3:
                                hp.hp = 0
                            else:
                                hp.hp -= 3
                            heart.invincible = True

                elif attack_rand == 1:  
                    """
                    バウンドビームの作成
                    """
                    if attack_tmr == 0:
                        for _ in range(6):
                            start_pos = (WIDTH//2,HEIGHT//2-35)
                            bound_beam.add(Bound_Beam((255,255,255),start_pos))
                    if len(pg.sprite.spritecollide(heart, bound_beam, False)) != 0:
                        if heart.invincible == False:
                            if hp.hp < 3:
                                hp.hp = 0
                            else:
                                hp.hp -= 2
                            heart.invincible = True

                elif attack_rand == 2:
                    """
                    上下左右ビームの作成
                    """
                    if attack_tmr % 10 == 0:
                        start_pos2 = (0,random.randint(HEIGHT/2-50,HEIGHT/2+250))
                        speed = (+20, 0)
                        beamw.add(Beam((255, 255, 255), start_pos2, speed))
                    if attack_tmr % 10 == 0:
                        speed = (0, +20)
                        start_pos2 = (random.randint(WIDTH/2-150,WIDTH/2+150),0)
                        beamh.add(Beam((255, 255, 255), start_pos2,speed,True))
                    #ビームとの衝突判定
                    if len(pg.sprite.spritecollide(heart, beamw, False)) != 0 or len(pg.sprite.spritecollide(heart, beamh, False)) != 0:
                        if heart.invincible == False:
                            if hp.hp < 3:
                                hp.hp = 0
                            else:
                                hp.hp -= 2
                            heart.invincible = True
                
                elif attack_rand == 3:
                    """
                    予告ビームと横からビームの作成
                    """
                    # 横からビームの発生
                    if attack_tmr % 40 == 0:  # 一定時間ごとにビームを生成
                        start_pos = (WIDTH/2, random.choice([HEIGHT/2, HEIGHT/2+100, HEIGHT/2+200]))
                        # 予告ビームの表示
                        sidebeamf.add(SideBeamFake(start_pos))
                    elif attack_tmr % 40 == 39:
                        # 横からビームの表示
                        sidebeamr.add(SideWallReal(start_pos))
                    # ビームとの衝突判定
                    if len(pg.sprite.spritecollide(heart, sidebeamr, False)) != 0:
                        if heart.invincible == False:
                            if hp.hp < 4:
                                hp.hp = 0
                            else:
                                hp.hp -= 5
                            heart.invincible = True
                
                elif attack_rand == 4:
                    """
                    地雷原の作成
                    """
                    if (attack_tmr + 1) % 30 == 0: # haiti
                        minefield.place_bombs()
                    elif (attack_tmr + 1) % 30 == 21: # bakuha
                        explosion.create_explosions(minefield.bombs)

                    if 0 <= (attack_tmr + 1) % 30 <= 22: # next
                        minefield.draw()
                    else: 
                        explosion.draw()
                    
                    if attack_tmr > 40:
                        if pg.sprite.spritecollide(heart, explosion.explosions, False) and not heart.invincible:
                            if hp.hp < 3:
                                hp.hp = 0
                            else:
                                hp.hp -= 1
                            heart.invincible = True
                
                elif attack_rand == 5:
                    """
                    卵ぶんぶん
                    """
                    if attack_tmr % 4 == 0:
                        # pass
                        dream_egg.add(DreamEgg(kkton, heart))
                    if len(pg.sprite.spritecollide(heart, dream_egg, False)) != 0:
                        if heart.invincible == False:
                            if hp.hp < 3:
                                hp.hp = 0
                            else:
                                hp.hp -= 1
                            heart.invincible = True

                elif attack_rand == 6:
                    """
                    中心大回転ビーム
                    """
                    if attack_tmr % 4 == 0:
                        pi_lst = [i * math.pi/14 for i in range(0, 14*2-1)]
                        num = pi_lst[rand%(14*2-1)]
                        x = math.cos(num)*200
                        y = math.sin(num)*200

                        start_pos = (WIDTH/2+x, HEIGHT/2+50+y)
                        follow_bream.add(FollowingBeam(heart, start_pos, 0))
                        rand += 1

                    if len(pg.sprite.spritecollide(heart, follow_bream, False)) != 0:
                        for beam in follow_bream:
                            if pg.sprite.collide_mask(heart, beam):
                                if heart.invincible == False:
                                    if hp.hp < 3:
                                        hp.hp = 0
                                    else:
                                        hp.hp -= 5
                                    heart.invincible = True

                elif attack_rand == 7:
                    """
                    追従ビーム
                    """
                    if attack_tmr % 15 == 0:
                        pi_lst = [i * math.pi/14 for i in range(0, 14*2-1)]
                        num = pi_lst[random.randint(0, len(pi_lst)-1)]
                        x = math.cos(num)*200
                        y = math.sin(num)*200

                        start_pos = (heart.rect.centerx+x, heart.rect.centery+y)
                        follow_bream.add(FollowingBeam(heart, start_pos, 0, True))

                    if len(pg.sprite.spritecollide(heart, follow_bream, False)) != 0:
                        for beam in follow_bream:
                            if pg.sprite.collide_mask(heart, beam):
                                if heart.invincible == False:
                                    if hp.hp < 3:
                                        hp.hp = 0
                                    else:
                                        hp.hp -= 2
                                    heart.invincible = True

                """
                クラスの更新を行う
                """
                # 以下に攻撃に関するクラスの更新
                
                sidebeamf.update(screen)

                kkton.update(screen)
                key_lst = pg.key.get_pressed()
                heart.update(key_lst, screen)
                hp.draw(screen)
                choice.draw(screen, True)
                hp.update()
                rakutan.update(screen)
                bound_beam.update(screen)
                beamw.update(screen)
                beamh.update(screen)
                sidebeamr.update(screen)
                dream_egg.update(screen)
                follow_bream.update(screen)
                
                if attack_tmr > 300: # 選択画面に戻る
                    """
                    タイマーが300以上になったら選択画面に戻るように設定している。
                    """
                    dialog.update(screen, True)
                    # 初期化
                    heart = Heart((WIDTH/2, HEIGHT/2+100))
                    rakutan.update(screen, True)
                    sidebeamr.update(screen, True)
                    sidebeamf.update(screen, True)
                    beamw.update(screen, True)
                    beamh.update(screen, True)
                    bound_beam.update(screen,True)
                    dream_egg.update(screen, True)
                    follow_bream.update(screen, True)
                    kkton.rect.centerx = WIDTH/2
                    gameschange = 0
                    select_tmr = 0
                    talk.index = 0
                    no_attack_num += 1
                attack_tmr += 1

            elif gameschange == 4:  # 「こうどう」を選択した場合
                """
                どの行動をとるのかの選択を表示する
                """
                # キー操作による状態遷移
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return
                    elif event.type == pg.KEYDOWN:
                        choice_action.update(event.key)
                        if event.key == pg.K_ESCAPE:
                            select_voice.play(0)
                            gameschange = 0
                        if event.key == pg.K_RETURN:  # エンターキーを押されたら
                            if choice_action.index == 0:
                                select_voice.play(0)
                                gameschange = 6
                            elif choice_action.index == 1:
                                select_voice.play(0)
                                gameschange = 7
                            elif choice_action.index == 2:
                                select_voice.play(0)
                                gameschange = 8
                            elif choice_action.index == 3:
                                select_voice.play(0)
                                gameschange = 9 

                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)
                kkton.update(screen)  # こうかとんの描画
                choice_action.draw(screen)  # 行動の選択肢の描画
                hp.draw(screen)  # 体力バーの描画
                choice.draw(screen)  # 選択肢の更新

            elif gameschange == 5:  # 「アイテム」の画面
                """
                どのアイテムを選ぶのかの選択を表示する
                """
                # キー操作による状態遷移
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return
                    elif event.type == pg.KEYDOWN:
                        choice_item.update(event.key)
                        if event.key == pg.K_ESCAPE:
                            select_voice.play(0)
                            gameschange = 0
                        if event.key == pg.K_RETURN:  # エンターキーを押されたら
                            item.cure(hp, choice_item_lst[choice_item.index], choice_item_lst)
                            if item.next:
                                choice_item.index = 0
                                gameschange=3

                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)
                kkton.update(screen)  # こうかとんの描画
                choice_item.draw(screen)  # アイテムの描画
                hp.draw(screen)  # 体力の描画
                choice.draw(screen)  # 選択肢の描画

            elif gameschange == 6:  # 分析の選択
                """
                「こうかとんを分析する」を選択した後の画面の表示
                """
                # キー操作による状態遷移
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return
                    elif event.type == pg.KEYDOWN:
                        if event.key == pg.K_RETURN:
                                select_voice.play(0)
                                gameschange = 3

                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)
                # 選択肢後の画面に関する初期化
                afterchoice = AfterChoice(["こうかとん:Attack 3 Diffence 100", "こうかとん、それはこの世の支配者、、、"])   
                kkton.update(screen)
                # 選択画面の表示
                afterchoice.draw(screen, True)
                # 体力バーの更新
                hp.draw(screen)
                hp.update()
                # 選択肢の更新
                choice.draw(screen)

            elif gameschange == 7:  # 話すの選択
                """
                「こうかとんと話す」を選択した後の画面の表示
                """
                # キー操作による状態遷移
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return
                    elif event.type == pg.KEYDOWN:
                        if event.key == pg.K_RETURN:
                                select_voice.play(0)
                                gameschange = 3
                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)
                # 選択肢後の画面に関する初期化
                afterchoice = AfterChoice(["こうかとんは、話を聞いてくれないようだ", "こうかとん：「貴様ごときが口を開くな」"])   
                kkton.update(screen)
                # 選択画面の表示
                afterchoice.draw(screen, True)
                # 体力バーの更新
                hp.draw(screen)
                hp.update()
                # 選択肢の更新
                choice.draw(screen)

            elif gameschange == 8:  # 焼くの選択
                """
                「こうかとんを焼く」を選択した後の画面の表示
                """
                # キー操作による状態遷移
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return
                    elif event.type == pg.KEYDOWN:
                        if event.key == pg.K_RETURN:
                                select_voice.play(0)
                                gameschange = 3

                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)
                # 選択肢後の画面に関する初期化
                afterchoice = AfterChoice(["こうかとんにそんなことをしてはいけない", "こうかとん：「なめた物言いだな、、、」"])   
                kkton.update(screen)
                # 選択画面の表示
                afterchoice.draw(screen, True)
                # 体力バーの更新
                hp.draw(screen)
                hp.update()
                # 選択肢の更新
                choice.draw(screen)

            elif gameschange == 9:  # 説得の選択
                """
                「こうかとんを説得する」を選択した後の画面の表示
                """
                # キー操作による状態遷移
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return
                    elif event.type == pg.KEYDOWN:
                        if event.key == pg.K_RETURN:
                                select_voice.play(0)
                                gameschange = 3
                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)
                # 選択肢後の画面に関する初期化
                afterchoice = AfterChoice(["こうかとんは聞く耳を持たない", "こうかとん：「ふんっ」"])   
                kkton.update(screen)
                # 選択画面の表示
                afterchoice.draw(screen, True)
                # 体力バーの更新
                hp.draw(screen)
                # 選択肢の更新
                choice.draw(screen)

            elif gameschange == 10:  # 「みのがす」を選択した場合
                # キー操作による状態遷移
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return
                    elif event.type == pg.KEYDOWN:
                        if event.key == pg.K_ESCAPE:
                            gameschange = 0
                        elif event.key == pg.K_RETURN:
                            select_voice.play(0)
                            gameschange = 11

                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)  # 大枠を描画
                choice_escape.draw(screen)  # 渡したリストを表示
                kkton.update(screen)  # こうかとんの表示
                hp.draw(screen)  # 残り体力の描画
                choice.draw(screen)  # 選択肢の更新
            
            elif gameschange == 11:  # にがすを選択(にがせない場合)
                # キー操作による状態遷移
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return
                    elif event.type == pg.KEYDOWN:
                        if event.key == pg.K_RETURN:
                            select_voice.play(0)
                            gameschange = 3
                
                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)
                if no_attack and no_attack_num > end_judg:
                    gameschange = 12
                    sound.stop()
                else:
                    print(no_attack_num)
                    afterchoice = AfterChoice(["＊　にがせない !", "＊　こうかとんはにやにやしている"])
                    afterchoice.draw(screen, True)
                kkton.update(screen)  # こうかとんの表示
                hp.draw(screen)
                choice.draw(screen)

            elif gameschange == 12:
                # キー操作による状態遷移
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return
                    elif event.type == pg.KEYDOWN:
                        if event.key == pg.K_RETURN:
                            # if no_attack == False
                            select_voice.play(0)
                            return

                pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)
                afterchoice = AfterChoice(["＊　YOU WIN !", "＊　GPAと単位を かくとく！"])
                afterchoice.draw(screen, True)
                kkton.update(screen)  # こうかとんの表示
                hp.draw(screen)
                choice.draw(screen)

        elif scenechange == 2:  # ゲームオーバー画面
            """
            ゲームオーバーシーン
            プレイヤーのHPが0以下になったら実行される
            """
            # キー操作による状態遷移
            for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return
                    elif event.type == pg.KEYDOWN:
                        if event.key == pg.K_RETURN:
                            restart = True

            if gameover_tmr < 50:
                breakheart.update(screen)
            elif gameover_tmr == 50:
                sound = pg.mixer.Sound("./sound/gameover.mp3")
                sound.play(-1)
            elif 50 < gameover_tmr:
                gameov.update(screen)
            if gameover_tmr > 100 and restart:
                # 怒涛の初期化
                sound.stop()
                heart = Heart((WIDTH/2, HEIGHT/2+100))
                rakutan.update(screen, True)
                dream_egg.update(screen, True)
                follow_bream.update(screen, True)
                rakutan.update(screen, True)
                beamw.update(screen, True)
                beamh.update(screen, True)
                bound_beam.update(screen,True)
                sidebeamr.update(screen, True)
                sidebeamf.update(screen, True)
                rakutan.update(screen, True)
                kkton.rect.centerx = WIDTH/2
                hp =HealthBar(WIDTH/4, 5*HEIGHT/6, max_hp+4, max_hp, gpa)
                en_hp = EnemyHealthBar(WIDTH/2, HEIGHT/3, en_max_hp, en_max_hp)
                gameover_tmr = 0
                select_tmr = 0
                choice_item_lst = [
                    "＊　こうかとんエキス", 
                    "＊　こうかとんジュース", 
                    "＊　こうかとんエナジー", 
                    "＊　こうかとんドリンク",
                    ]
                choice_item = (AfterChoice(choice_item_lst))
                gameov.update(screen, True)
                sound = pg.mixer.Sound("./sound/Megalovania.mp3")
                sound.play(-1)
                talk.index = 0
                no_attack: bool = True  # 一度でも攻撃したかどうか
                no_attack_num = 0  # 何回攻撃されたか
                gameschange = 0
                scenechange = 1
                restart = False
            gameover_tmr += 1

        elif scenechange == 3:  # ゲームエンド画面
            """
            ゲーム終了
            """
            # キー操作による状態遷移
            for event in pg.event.get():
                    if event.type == pg.QUIT:
                        return
            pg.draw.rect(screen,(255,255,255), Rect(10, HEIGHT/2-50, WIDTH-20, 300), 5)
            gameend_atk.update(screen)
            hp.draw(screen)
            if gameend_atk.gameend:
                return
                
        pg.display.update()
        clock.tick(30)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
