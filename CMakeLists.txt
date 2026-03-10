cmake_minimum_required(VERSION 3.7)
project(sim_indirect_dual_priv)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-deprecated-declarations")

#set(CMAKE_VERBOSE_MAKEFILE 1)

if(APPLE AND CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
  set(_libomp_prefixes
      /opt/homebrew/opt/libomp
      /usr/local/opt/libomp)
  foreach(_libomp_prefix IN LISTS _libomp_prefixes)
    if(EXISTS "${_libomp_prefix}/include/omp.h" AND EXISTS "${_libomp_prefix}/lib/libomp.dylib")
      set(OpenMP_C_FLAGS "-Xpreprocessor -fopenmp -I${_libomp_prefix}/include" CACHE STRING "OpenMP C flags" FORCE)
      set(OpenMP_C_LIB_NAMES "omp" CACHE STRING "OpenMP C libs" FORCE)
      set(OpenMP_CXX_FLAGS "-Xpreprocessor -fopenmp -I${_libomp_prefix}/include" CACHE STRING "OpenMP CXX flags" FORCE)
      set(OpenMP_CXX_LIB_NAMES "omp" CACHE STRING "OpenMP CXX libs" FORCE)
      set(OpenMP_omp_LIBRARY "${_libomp_prefix}/lib/libomp.dylib" CACHE FILEPATH "OpenMP libomp library" FORCE)
      break()
    endif()
  endforeach()
endif()

find_package(OpenMP REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(MPI REQUIRED)
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

add_executable(main_RecoveryAnalysis main_RecoveryAnalysis.cpp Norm.hpp)
target_link_libraries(main_RecoveryAnalysis OpenMP::OpenMP_CXX nlohmann_json::nlohmann_json)

add_executable(main_SweepR2 main_SweepR2.cpp EvolPrivRepGame.hpp PrivRepGame.hpp Norm.hpp)
target_link_libraries(main_SweepR2 Eigen3::Eigen OpenMP::OpenMP_CXX nlohmann_json::nlohmann_json)

add_executable(main_ExhaustiveSearch main_ExhaustiveSearch.cpp EvolPrivRepGame.hpp PrivRepGame.hpp Norm.hpp)
target_link_libraries(main_ExhaustiveSearch Eigen3::Eigen OpenMP::OpenMP_CXX nlohmann_json::nlohmann_json MPI::MPI_CXX)
