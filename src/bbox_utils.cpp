#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // For std::vector, std::string, etc.
#include <random>
#include <string>
#include <iomanip> // For std::hex, std::setfill, std::setw
#include <sstream> // For std::stringstream

namespace py = pybind11;

// Structure to represent a bounding box in normalized (YOLO) format
struct NormalizedBoundingBox
{
    int class_id;
    double center_x;
    double center_y;
    double width;
    double height;
};

// Structure to represent a bounding box in pixel (QRectF) format
struct PixelBoundingBox
{
    int class_id;
    double x;
    double y;
    double width;
    double height;
};

// Function to convert pixel bounding boxes to normalized YOLO format
std::vector<NormalizedBoundingBox> convert_to_yolo_format(
    const std::vector<PixelBoundingBox> &pixel_boxes,
    double original_width,
    double original_height)
{

    std::vector<NormalizedBoundingBox> yolo_boxes;
    for (const auto &p_box : pixel_boxes)
    {
        if (p_box.width <= 0 || p_box.height <= 0)
        {
            continue;
        }

        double center_x = (p_box.x + p_box.width / 2) / original_width;
        double center_y = (p_box.y + p_box.height / 2) / original_height;
        double width = p_box.width / original_width;
        double height = p_box.height / original_height;

        yolo_boxes.push_back({p_box.class_id, center_x, center_y, width, height});
    }
    return yolo_boxes;
}

// Function to convert normalized YOLO bounding boxes to pixel format
std::vector<PixelBoundingBox> convert_from_yolo_format(
    const std::vector<NormalizedBoundingBox> &yolo_boxes,
    double original_width,
    double original_height)
{

    std::vector<PixelBoundingBox> pixel_boxes;
    for (const auto &n_box : yolo_boxes)
    {
        double x = (n_box.center_x - n_box.width / 2) * original_width;
        double y = (n_box.center_y - n_box.height / 2) * original_height;
        double w = n_box.width * original_width;
        double h = n_box.height * original_height;

        pixel_boxes.push_back({n_box.class_id, x, y, w, h});
    }
    return pixel_boxes;
}

// Random number generator for colors
std::random_device rd;
std::mt19937 gen(rd());

// Function to generate a random color in hex string format
std::string generate_random_color()
{
    std::uniform_int_distribution<> distrib(0, 255);
    int r = 0, g = 0, b = 0;

    // Ensure reasonable brightness (not too dark or too light)
    // This is a simplified version of the Python logic, aiming for a mid-range brightness
    while ((r + g + b < 300) || (r + g + b > 600))
    {
        r = distrib(gen);
        g = distrib(gen);
        b = distrib(gen);
    }

    std::stringstream ss;
    ss << "#" << std::hex << std::setfill('0') << std::setw(2) << r
       << std::setfill('0') << std::setw(2) << g
       << std::setfill('0') << std::setw(2) << b;
    return ss.str();
}

// Function to process raw YOLO results into a list of PixelBoundingBox
std::vector<PixelBoundingBox> process_yolo_results(
    const std::vector<std::vector<double>> &raw_boxes, // Each inner vector: [x1, y1, x2, y2, conf, class_id]
    double confidence_threshold)
{

    std::vector<PixelBoundingBox> new_boxes;
    for (const auto &box_data : raw_boxes)
    {
        if (box_data.size() >= 6)
        {
            double x1 = box_data[0];
            double y1 = box_data[1];
            double x2 = box_data[2];
            double y2 = box_data[3];
            double conf = box_data[4];
            int class_id = static_cast<int>(box_data[5]);

            if (conf > confidence_threshold)
            {
                double w = x2 - x1;
                double h = y2 - y1;
                new_boxes.push_back({class_id, x1, y1, w, h});
            }
        }
    }
    return new_boxes;
}

// Function to format a list of NormalizedBoundingBox objects into a single string
std::string format_yolo_labels_to_string(const std::vector<NormalizedBoundingBox> &yolo_boxes)
{
    std::stringstream ss;
    for (const auto &y_box : yolo_boxes)
    {
        ss << y_box.class_id << " "
           << std::fixed << std::setprecision(6) << y_box.center_x << " "
           << std::fixed << std::setprecision(6) << y_box.center_y << " "
           << std::fixed << std::setprecision(6) << y_box.width << " "
           << std::fixed << std::setprecision(6) << y_box.height << "\n";
    }
    return ss.str();
}

PYBIND11_MODULE(bbox_utils, m)
{
    m.doc() = "pybind11 plugin for bounding box utilities"; // optional module docstring

    py::class_<NormalizedBoundingBox>(m, "NormalizedBoundingBox")
        .def(py::init<>())
        .def_readwrite("class_id", &NormalizedBoundingBox::class_id)
        .def_readwrite("center_x", &NormalizedBoundingBox::center_x)
        .def_readwrite("center_y", &NormalizedBoundingBox::center_y)
        .def_readwrite("width", &NormalizedBoundingBox::width)
        .def_readwrite("height", &NormalizedBoundingBox::height);

    py::class_<PixelBoundingBox>(m, "PixelBoundingBox")
        .def(py::init<>())
        .def_readwrite("class_id", &PixelBoundingBox::class_id)
        .def_readwrite("x", &PixelBoundingBox::x)
        .def_readwrite("y", &PixelBoundingBox::y)
        .def_readwrite("width", &PixelBoundingBox::width)
        .def_readwrite("height", &PixelBoundingBox::height);

    m.def("convert_to_yolo_format", &convert_to_yolo_format,
          "A function that converts pixel bounding boxes to normalized YOLO format.");

    m.def("convert_from_yolo_format", &convert_from_yolo_format,
          "A function that converts normalized YOLO bounding boxes to pixel format.");

    m.def("generate_random_color", &generate_random_color,
          "A function that generates a random color in hex string format.");

    m.def("process_yolo_results", &process_yolo_results,
          "A function that processes raw YOLO detection results, filters by confidence, and converts to pixel bounding boxes.");

    m.def("format_yolo_labels_to_string", &format_yolo_labels_to_string,
          "A function that formats a list of normalized bounding boxes into a YOLO .txt file string.");
}
