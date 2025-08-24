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
}
