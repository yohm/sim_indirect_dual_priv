# CMake generated Testfile for 
# Source directory: /home/user/sim_indirect_dual_priv
# Build directory: /home/user/sim_indirect_dual_priv/cmake-build-release
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(test_Norm "/home/user/sim_indirect_dual_priv/cmake-build-release/test_Norm")
set_tests_properties(test_Norm PROPERTIES  _BACKTRACE_TRIPLES "/home/user/sim_indirect_dual_priv/CMakeLists.txt;27;add_test;/home/user/sim_indirect_dual_priv/CMakeLists.txt;0;")
add_test(test_PublicRepGame "/home/user/sim_indirect_dual_priv/cmake-build-release/test_PublicRepGame")
set_tests_properties(test_PublicRepGame PROPERTIES  _BACKTRACE_TRIPLES "/home/user/sim_indirect_dual_priv/CMakeLists.txt;31;add_test;/home/user/sim_indirect_dual_priv/CMakeLists.txt;0;")
add_test(test_PrivRepGame "/home/user/sim_indirect_dual_priv/cmake-build-release/test_PrivRepGame")
set_tests_properties(test_PrivRepGame PROPERTIES  _BACKTRACE_TRIPLES "/home/user/sim_indirect_dual_priv/CMakeLists.txt;35;add_test;/home/user/sim_indirect_dual_priv/CMakeLists.txt;0;")
add_test(test_EvolPrivRepGame "/home/user/sim_indirect_dual_priv/cmake-build-release/test_EvolPrivRepGame")
set_tests_properties(test_EvolPrivRepGame PROPERTIES  _BACKTRACE_TRIPLES "/home/user/sim_indirect_dual_priv/CMakeLists.txt;39;add_test;/home/user/sim_indirect_dual_priv/CMakeLists.txt;0;")
subdirs("_deps/googletest-build")
