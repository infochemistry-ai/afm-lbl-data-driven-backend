cmake_minimum_required(VERSION 3.14)
project(lacunarity CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
find_package(GSL REQUIRED)
add_library(lacunarity SHARED
    source/main.cpp
    source/matrix_process.cpp
    source/memory_free.cpp
)
target_include_directories(lacunarity PUBLIC include)
target_link_libraries(lacunarity PRIVATE GSL::gsl GSL::gslcblas)
