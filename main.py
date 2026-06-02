import xml.etree.ElementTree as ET
import cv2
import uiautomator2 as u2

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

def get_screenshot(device):
    device.screenshot("screenshot.png")

def get_nodes_with_clickable(root):
    return [node for node in root.iter("node") if node.attrib.get("clickable") == "true"]

def build_node_data(node):
    bounds_attr = node.attrib.get("bounds")
    if not bounds_attr:
        return None

    left, top, right, bottom = bounds_to_coordinates(bounds_attr)
    center_x, center_y = center_of_bounds(left, top, right, bottom)

    return {
        "node": node,
        "left": left,
        "top": top,
        "right": right,
        "bottom": bottom,
        "center_x": center_x,
        "center_y": center_y,
        "width": right - left,
        "height": bottom - top,
    }

def group_rows(nodes, tolerance=15):
    rows = []
    nodes = sorted(nodes, key=lambda x: x["center_y"])
    for node in nodes:
        found = False
        for row in rows:
            if abs(row["center_y"] - node["center_y"]) <= tolerance:
                row["nodes"].append(node)
                found = True
                break

        if not found:
            rows.append({"center_y": node["center_y"], "nodes": [node]})
            
    final_rows = []
    for row in rows:
        row["nodes"].sort(key=lambda x: x["left"])
        final_rows.append(row["nodes"])

    return final_rows

def find_row_to_adjust(rows):
    consecutive_tens = 0
    for idx, row in enumerate(rows):
        if len(row) == 10:
            consecutive_tens += 1
        else:
            if consecutive_tens >= 1:
                return idx
            consecutive_tens = 0
    return None

def get_reference_width(row):
    if len(row) < 3:
        return None
    widths = [item["width"] for item in row[1:-1]]
    return round(sum(widths) / len(widths))

def adjust_row(row):
    reference_width = get_reference_width(row)
    if reference_width is None:
        return

    first = row[0]
    last = row[-1]
    first["left"] = first["right"] - reference_width
    first["width"] = reference_width
    last["right"] = last["left"] + reference_width
    last["width"] = reference_width
    first["center_x"], _ = center_of_bounds(first["left"], first["top"], first["right"], first["bottom"])
    last["center_x"], _ = center_of_bounds(last["left"], last["top"], last["right"], last["bottom"])

def draw_single_node(image, item):
    """Função única criada para envelopar e remover a repetição de desenho."""
    screen_height, screen_width, _ = image.shape
    relative_x, relative_y = relative_position(item["center_x"], item["center_y"], screen_width, screen_height)
    cv2.rectangle(image, (item["left"], item["top"]), (item["right"], item["bottom"]), (0, 255, 0), 2)
    text_x_str = f"X: {round(relative_x*100, 1)}%"
    text_y_str = f"Y: {round(relative_y*100, 1)}%"
    (text_w, text_h), _ = cv2.getTextSize(text_y_str, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
    text_x_pos = item["left"] + 5
    text_y_pos = item["left"] + 5
    pos_y_for_x = item["top"] + 15
    pos_y_for_y = item["top"] + text_h + 22 
    cv2.putText(image, text_x_str, (text_x_pos, pos_y_for_x), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
    cv2.putText(image, text_y_str, (text_y_pos, pos_y_for_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

def image_processing(image, root, correction_enabled=False):
    clickable_nodes = get_nodes_with_clickable(root)
    nodes = []
    for node in clickable_nodes:
        data = build_node_data(node)
        if data:
            nodes.append(data)

    if correction_enabled:
        rows = group_rows(nodes)
        row_to_adjust = find_row_to_adjust(rows)
        
        if row_to_adjust is not None:
            adjust_row(rows[row_to_adjust])
            
        for row in rows:
            for item in row:
                draw_single_node(image, item)
    else:
        for item in nodes:
            draw_single_node(image, item)
            
    cv2.imwrite("result.png", image)


if __name__ == "__main__":
    try:
        d = u2.connect()

        xml = d.dump_hierarchy()
        root = ET.fromstring(xml)

        get_screenshot(d)
        image = cv2.imread("screenshot.png")

        if image is None:
            print("Erro ao carregar screenshot.")
            exit()

        image_processing(image=image, root=root, correction_enabled=True)

        print("\nSuccess! Verify result.png")

    except Exception as e:
        print(f"Error: {e}")