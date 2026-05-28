import xml.etree.ElementTree as ET
import uiautomator2 as u2
import cv2

d = u2.connect()

xml = d.dump_hierarchy()
root = ET.fromstring(xml)
width, height = d.window_size()

def center_of_bounds(left, top, right, bottom):
    center_x = (left + right) // 2
    center_y = (top + bottom) // 2
    return center_x, center_y

def bounds_to_coordinates(bounds_str):
    cleaned = bounds_str.replace("[", "").replace("]", ",").split(",")
    cleaned = [x for x in cleaned if x != ""]
    
    left, top, right, bottom = map(int, cleaned)
    return left, top, right, bottom

def relative_position(center_x, center_y, screen_width, screen_height):
    relative_x = center_x / screen_width
    relative_y = center_y / screen_height
    return relative_x, relative_y

def get_screenshot():
    d.screenshot("screenshot.png")

get_screenshot()
image = cv2.imread("screenshot.png")

for node in root.iter("node"):
    if node.attrib.get("clickable") == "true":
        bounds_attr = node.attrib.get("bounds")
        if not bounds_attr:
            continue
            
        left, top, right, bottom = bounds_to_coordinates(bounds_attr)
        center = center_of_bounds(left, top, right, bottom)
        relative_x, relative_y = relative_position(center[0], center[1], width, height)

        cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
        
        text_x_str = f"X: {round(relative_x*100, 1)}%"
        text_y_str = f"Y: {round(relative_y*100, 1)}%"
        
        size_x, _ = cv2.getTextSize(text_x_str, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        size_y, _ = cv2.getTextSize(text_y_str, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        
        text_x_pos = left + 5
        text_y_pos = left + 5
        
        rect_center_y = top + (bottom - top) // 2

        pos_y_for_x = top + 20  # Desloca 2 pixels para cima
        pos_y_for_y = top + size_y[1] + 25  # Desloca para baixo considerando a altura da fonte
        
        cv2.putText(image, text_x_str, (text_x_pos, pos_y_for_x), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
        cv2.putText(image, text_y_str, (text_y_pos, pos_y_for_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

cv2.imwrite("resultado.png", image)