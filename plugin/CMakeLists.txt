cmake_minimum_required(VERSION 3.10)
project(definition CXX)
set(CMAKE_CXX_STANDARD 17)

execute_process(
        COMMAND ${CMAKE_CXX_COMPILER} -print-file-name=plugin
        RESULT_VARIABLE COMPILER_PLUGIN_RESULT
        OUTPUT_VARIABLE COMPILER_PLUGIN_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
)

if(NOT COMPILER_PLUGIN_RESULT EQUAL 0 OR COMPILER_PLUGIN_DIR STREQUAL "")
    message(FATAL_ERROR "Failed to get plugin directory from ${CMAKE_CXX_COMPILER}")
endif()

message(STATUS "Compiler plugin dir: ${COMPILER_PLUGIN_DIR}")

add_library(shared_code STATIC src/config_parser.cpp src/get_arg_config.cpp)
target_include_directories(shared_code PRIVATE ${CMAKE_SOURCE_DIR}/include ${COMPILER_PLUGIN_DIR}/include)
target_compile_options(shared_code PRIVATE -fno-rtti -fPIC)

function(create_plugin plugin_name)
    add_library(${plugin_name} SHARED src/${plugin_name}.cpp)

    set_target_properties(${plugin_name} PROPERTIES
            PREFIX ""
            OUTPUT_NAME ${plugin_name}
    )

    target_include_directories(${plugin_name} PRIVATE ${CMAKE_SOURCE_DIR}/include ${COMPILER_PLUGIN_DIR}/include)
    target_compile_options(${plugin_name} PRIVATE -fno-rtti)

    target_link_libraries(${plugin_name} PRIVATE shared_code)
endfunction()

create_plugin(cxx_optimizer)
