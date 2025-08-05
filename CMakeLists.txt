cmake_minimum_required(VERSION 3.7)
project(sim_indirect_dual_priv)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-deprecated-declarations")

#set(CMAKE_VERBOSE_MAKEFILE 1)

find_package(OpenMP REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(nlohmann_json REQUIRED)
include_directories(${CMAKE_SOURCE_DIR}/icecream-cpp)

# See http://google.github.io/googletest/quickstart-cmake.html
include(FetchContent)
FetchContent_Declare(
        googletest
        URL https://github.com/google/googletest/archive/03597a01ee50ed33e9dfd640b249b4be3799d395.zip
)
# For Windows: Prevent overriding the parent project's compiler/linker settings
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)


add_executable(main_well_mixed_evo main_well_mixed_evo.cpp Norm.hpp PrivRepGame.hpp EvolPrivRepGame.hpp)
target_link_libraries(main_well_mixed_evo Eigen3::Eigen nlohmann_json::nlohmann_json)

add_executable(test_Norm test_Norm.cpp Norm.hpp)
target_link_libraries(test_Norm GTest::gtest_main)
add_test(NAME test_Norm COMMAND test_Norm)

add_executable(test_PublicRepGame test_PublicRepGame.cpp PublicRepGame.hpp Norm.hpp)
target_link_libraries(test_PublicRepGame GTest::gtest_main)
add_test(NAME test_PublicRepGame COMMAND test_PublicRepGame)

add_executable(test_PrivRepGame test_PrivRepGame.cpp PrivRepGame.hpp Norm.hpp)
target_link_libraries(test_PrivRepGame GTest::gtest_main)
add_test(NAME test_PrivRepGame COMMAND test_PrivRepGame)

add_executable(test_EvolPrivRepGame test_EvolPrivRepGame.cpp EvolPrivRepGame.hpp PrivRepGame.hpp Norm.hpp)
target_link_libraries(test_EvolPrivRepGame OpenMP::OpenMP_CXX Eigen3::Eigen nlohmann_json::nlohmann_json GTest::gtest_main)
add_test(NAME test_EvolPrivRepGame COMMAND test_EvolPrivRepGame)

enable_testing()

add_executable(inspect_Norm inspect_Norm.cpp Norm.hpp)

add_executable(inspect_PublicRepGame inspect_PublicRepGame.cpp PublicRepGame.hpp Norm.hpp)

add_executable(inspect_PrivRepGame inspect_PrivRepGame.cpp PrivRepGame.hpp Norm.hpp)
target_link_libraries(inspect_PrivRepGame nlohmann_json::nlohmann_json)

add_executable(inspect_EvolPrivRepGame inspect_EvolPrivRepGame.cpp EvolPrivRepGame.hpp PrivRepGame.hpp Norm.hpp)
target_link_libraries(inspect_EvolPrivRepGame Eigen3::Eigen OpenMP::OpenMP_CXX nlohmann_json::nlohmann_json)
