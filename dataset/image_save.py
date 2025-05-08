import cv2
import os
import yaml
import time

class MultiCamRecorder:
    def __init__(self):
        self.cam_paths = ["/dev/cam1", "/dev/cam2", "/dev/cam3", "/dev/cam4"]
        self.caps = [cv2.VideoCapture(p) for p in self.cam_paths]
        self.dataset_root = "dataset"
        self.image_dir = os.path.join(self.dataset_root, "image")
        self.label_dir = os.path.join(self.dataset_root, "label")
        self.counter = self.get_last_index() + 1
        
        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.label_dir, exist_ok=True)
        
        self.input_mode = False
        self.current_input = ""
        self.input_target = None  # 'force_z' or 'label'
        self.saved_frames = None

    def get_last_index(self):
        try:
            return max([int(d) for d in os.listdir(self.image_dir) if d.isdigit()])
        except:
            return 0

    def save_frame(self, frames, folder_name):
        save_dir = os.path.join(self.image_dir, folder_name)
        os.makedirs(save_dir, exist_ok=True)
        
        for i, frame in enumerate(frames, 1):
            cv2.imwrite(os.path.join(save_dir, f"{i}.jpg"), frame)

    def create_label(self, folder_name, force_z, label):
        label_path = os.path.join(self.label_dir, f"{folder_name}.yaml")
        data = {
            "force_z": float(force_z),
            "label": int(label),
            "_comment": {
                "label": "0:草地, 1:沙地, 3:水泥地, 4:土地"
            }
        }
        with open(label_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

    def draw_input_prompt(self, display_frame):
        prompt = f"Enter {self.input_target}: {self.current_input}"
        cv2.putText(display_frame, prompt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display_frame, "Press ENTER to confirm, BACKSPACE to delete", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        return display_frame

    def handle_input(self, key):
        if key == 13:  # Enter
            return True
        elif key == 8:  # Backspace
            self.current_input = self.current_input[:-1]
        elif 48 <= key <= 57:  # 0-9
            self.current_input += chr(key)
        elif key == 46:  # Decimal point
            if '.' not in self.current_input:
                self.current_input += chr(key)
        return False

    def run(self):
        print("程序启动，按空格键保存图像，按q退出")
        
        while True:
            if not self.input_mode:
                # 正常摄像头捕获流程
                frames = []
                rets = []
                
                for cap in self.caps:
                    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
                    ret, frame = cap.read()
                    rets.append(ret)
                    if ret:
                        frames.append(frame)
                
                if all(rets):
                    resized = [cv2.resize(f, (320, 240)) for f in frames]
                    top = cv2.hconcat(resized[:2])
                    bottom = cv2.hconcat(resized[2:])
                    display = cv2.vconcat([top, bottom])
                    cv2.imshow('Multi Camera', display)
            
            key = cv2.waitKey(1) & 0xFF
            
            if self.input_mode:
                # 输入处理模式
                if key != 255:  # 有按键按下
                    if self.handle_input(key):
                        if self.input_target == 'force_z':
                            self.force_z = self.current_input
                            self.current_input = ""
                            self.input_target = 'label'
                        else:
                            self.label = self.current_input
                            self.input_mode = False
                            try:
                                self.create_label(self.folder_name, self.force_z, self.label)
                                print(f"数据保存成功！{self.folder_name}")
                                self.counter += 1
                            except Exception as e:
                                print(f"输入错误: {e}")
                            finally:
                                self.saved_frames = None
                    # 更新显示输入提示
                    if all(rets):
                        display = cv2.vconcat([top, bottom])
                        display = self.draw_input_prompt(display)
                        cv2.imshow('Multi Camera', display)
            else:
                # 正常按键处理
                if key == ord(' '):
                    if all(rets):
                        self.folder_name = f"{self.counter:04d}"
                        self.save_frame(frames, self.folder_name)
                        self.saved_frames = frames
                        self.input_mode = True
                        self.input_target = 'force_z'
                        self.current_input = ""
                        print(f"\n保存到文件夹: {self.folder_name}")
                        # 进入输入模式后立即绘制提示
                        display = self.draw_input_prompt(display)
                        cv2.imshow('Multi Camera', display)
                elif key == ord('q'):
                    break
        
        # 释放资源
        for cap in self.caps:
            cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    recorder = MultiCamRecorder()
    recorder.run()
