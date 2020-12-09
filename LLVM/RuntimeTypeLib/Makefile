CXX_FLAGS= -Wall -Wextra -std=c++11

ir:
	clang++ $(CXX_FLAGS) -emit-llvm external_lib.cpp -S -o external_lib.ll
	clang++ $(CXX_FLAGS) -emit-llvm -c external_lib.cpp -o external_lib.bc

rir:
	clang++ $(CXX_FLAGS) -DPREDUCE -emit-llvm external_lib.cpp -S -o external_lib.ll
	clang++ $(CXX_FLAGS) -DPREDUCE -emit-llvm -c external_lib.cpp -o external_lib.bc	

test:
	clang++ $(CXX_FLAGS) -DPREDUCE external_lib.cpp test_main.cpp -o external_test.out

g++:
	g++ $(CXX_FLAGS) external_lib.cpp test_main.cpp -o g_external_test.out

clean:
	rm external_test.out external_lib.ll g_external_test.out