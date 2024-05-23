import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.clock import Clock
import cv2
import serial
import serial.tools.list_ports
from threading import Thread

class MainApp(App):
    def build(self):
        self.video_path = ""
        self.cap = None
        self.serial_port = None
        self.serial_connected = False

        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.title_label = Label(text='Chương trình mở video', font_size='24sp')
        self.layout.add_widget(self.title_label)

        self.path_input = TextInput(hint_text='Chọn video', readonly=True)
        self.layout.add_widget(self.path_input)

        self.choose_button = Button(text='CHỌN VIDEO', on_press=self.choose_video)
        self.layout.add_widget(self.choose_button)

        self.com_port_combo = TextInput(hint_text='Cổng COM')
        self.layout.add_widget(self.com_port_combo)

        self.reset_button = Button(text='Reset Cổng COM', on_press=self.reset_com_ports)
        self.layout.add_widget(self.reset_button)

        self.sensor_input = TextInput(hint_text='Nhập giá trị cảm biến', multiline=False)
        self.layout.add_widget(self.sensor_input)

        self.send_button = Button(text='Gửi giá trị cảm biến', on_press=self.send_to_arduino)
        self.layout.add_widget(self.send_button)

        self.play_button = Button(text='Phát Video', on_press=self.play_video)
        self.layout.add_widget(self.play_button)

        self.connect_button = Button(text='Kết nối', on_press=self.toggle_serial_connection)
        self.layout.add_widget(self.connect_button)

        self.stop_button = Button(text='Dừng Video', on_press=self.stop_video)
        self.layout.add_widget(self.stop_button)

        self.invalid_sensor_label = Label(text='', color=(1, 0, 0, 1))
        self.layout.add_widget(self.invalid_sensor_label)

        return self.layout

    def choose_video(self, instance):
        content = FileChooserListView()
        content.bind(on_selection=self.on_file_chosen)
        self.popup = Popup(title='Chọn tệp video', content=content, size_hint=(0.9, 0.9))
        self.popup.open()

    def on_file_chosen(self, instance, selection):
        if selection:
            self.video_path = selection[0]
            self.path_input.text = self.video_path
        self.popup.dismiss()

    def reset_com_ports(self, instance):
        self.com_port_combo.text = ''
        self.invalid_sensor_label.text = 'Cổng COM đã được Reset'
        Clock.schedule_once(self.clear_message, 2.5)

    def toggle_serial_connection(self, instance):
        if self.serial_connected:
            self.disconnect_serial_port()
        else:
            self.open_serial_port()

    def open_serial_port(self):
        try:
            self.serial_port = serial.Serial(self.com_port_combo.text, 115200, timeout=1)
            self.invalid_sensor_label.text = f"Đã mở cổng {self.com_port_combo.text}"
            self.serial_connected = True
            self.connect_button.text = 'Ngắt kết nối'
        except serial.SerialException:
            self.invalid_sensor_label.text = f"Không thể mở cổng {self.com_port_combo.text}"
            self.connect_button.text = 'Kết nối'
        Clock.schedule_once(self.clear_message, 2.5)

    def disconnect_serial_port(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.invalid_sensor_label.text = "Đã ngắt kết nối cổng COM"
            self.connect_button.text = 'Kết nối'
            self.serial_connected = False
        Clock.schedule_once(self.clear_message, 2.5)

    def send_to_arduino(self, instance):
        if self.serial_connected:
            sensor_value = self.sensor_input.text.strip()
            if sensor_value.isdigit():
                self.serial_port.write(f"{sensor_value}\n".encode())
                self.invalid_sensor_label.text = f"Đã gửi giá trị: {sensor_value}"
                self.sensor_input.text = ''
            else:
                self.invalid_sensor_label.text = "Giá trị cảm biến không hợp lệ. Vui lòng nhập một số nguyên hợp lệ."
            Clock.schedule_once(self.clear_message, 2.5)

    def play_video(self, instance):
        if not self.video_path:
            self.invalid_sensor_label.text = "Không thể mở video, vui lòng chọn video"
            Clock.schedule_once(self.clear_message, 2.5)
            return

        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            self.invalid_sensor_label.text = "Không thể mở video, vui lòng chọn video"
            Clock.schedule_once(self.clear_message, 2.5)
            return

        self.video_thread = Thread(target=self.update_video)
        self.video_thread.start()

    def update_video(self):
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                self.invalid_sensor_label.text = "Kết thúc video"
                Clock.schedule_once(self.clear_message, 2.5)
                break

            cv2.imshow('Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

    def stop_video(self, instance):
        if self.cap:
            self.cap.release()
            cv2.destroyAllWindows()

    def clear_message(self, dt):
        self.invalid_sensor_label.text = ''

if __name__ == '__main__':
    MainApp().run()
