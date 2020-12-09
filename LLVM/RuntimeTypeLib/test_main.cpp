#include "valueRecorder.h"
#include "function_call.h"

static std::vector<function_call*> funcs;
static std::vector<ir_type*> globs;

void test_update(uint8_t value, unsigned int index, unsigned int type){

	// std::cout << "NEW 8 " << value << std::endl;
	if (type == 0){
		if ( (globs.size() == 0) || (index > globs.size() - 1)){
			ir_type *temp = new i8_t(false,value);
			globs.push_back(temp);
			// delete temp;
		}else{
			ir_type *i8 = new i8_t(false, value);
			globs[index]->push(i8);
			// delete i8;
		}
	}else if (type == 1){
		funcs[index]->set_ret_value(new i8_t(false, value));
	}else if (type == 2){
		funcs[index]->set_arg_value(new i8_t(false, value));
	}
	return;
}

int main(){

	// { // block works fine
	// ir_type *test = new i8_t(false, 2);
	// i8_t *test2 = new i8_t(false, 3);
	// delete test;
	// delete test2;
	// }

	// { //block words fine
	//  *ptr = new ptr_t(2222);
	// ir_type *i8_pointed = new i8_t(false, 44);
	// ptr->push(i8_pointed);
	// delete ptr;}


	// { //block works fine
	// update_8(2, 0, 0);
	// update_8(2, 1, 0);
	// update_8(4, 2, 0);
	// deallocate();
	// }

	int a = record_invoke("main", "foo");
a = record_invoke("main", "foo");a = record_invoke("main", "foo");a = record_invoke("main", "foo");a = record_invoke("main", "foo");a = record_invoke("main", "foo");a = record_invoke("main", "foo");a = record_invoke("main", "foo");a = record_invoke("main", "foo");a = record_invoke("main", "foo");
	// int b = record_call("foo", "bar");
a = record_invoke("bar", "man");
	// update_ptr(123123, a, 1);
a = record_invoke("foo", "main");

	// update_array(4, a, 1);

	// update_ptr(11211, a, 1);
	// update_8(3, a, 1);
	// update_ptr(3111, a, 1);
	// update_8(5, a, 1);
	// update_ptr(4111, a, 1);
	// update_8(7, a, 1);
	// update_ptr(5111, a, 1);
	// update_8(9, a, 1);


	// update_ptr(123123, a, 2);

	// update_array(4, a, 2);

	// update_ptr(11211, a, 2);
	// update_8(3, a, 2);

	// update_ptr(3111, a, 2);
	// update_8(5, a, 2);


	// update_ptr(4111, a, 2);
	// update_8(7, a, 2);

	// update_ptr(5111, a, 2);
	// update_8(9, a, 2);

	print_trace();

	return 0;
}