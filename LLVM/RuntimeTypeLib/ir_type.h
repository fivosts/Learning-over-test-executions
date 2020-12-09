#include <iostream>
#include <stdio.h>
#include <unordered_set>
#include <algorithm>
#include <assert.h>

void strip_chars(std::string &str){

	std::unordered_set<char> unwanted_chars = {'\n', ',', '.', '{', '}'};
	int nl_counter = 0;
	for(unsigned i=0; i < str.length(); i++){
	    if(unwanted_chars.find(str[i]) != unwanted_chars.end()){
	        nl_counter++;//we increase the number of newlines we have found so far
	    }else{
	        str[i - nl_counter] = str[i];
	    }
	}
	str.resize(str.length() - nl_counter);

	return;
}

class ir_type{
public:
	ir_type(){}
	virtual ~ir_type(){}
	virtual bool is_signed(){return false;}
	virtual bool is_terminal(){return true;}
	virtual bool is_updated(){return true;}
	virtual bool is_undefined(){return false;}
	virtual bool is_possible_string(){return false;}
	virtual void represent_as_string(){}
	virtual void print(){}
	virtual void push(ir_type *t){
		(void) t;
		assert("Push method called, but from terminal type!");
	}

private:
};

class void_t : public ir_type{
public:
	void_t() : ir_type(){

	}
	void print() override{
		// std::cout << "void ";
		// std::cout << "0 ";
	}
	~void_t(){}

private:
};

class i1_t : public ir_type{
public:
	i1_t(bool val) : ir_type(){
		value = val;
	}
	~i1_t(){}
	void print() override{
		// std::cout << "bool " << value;
		// std::cout << value << " ";
	}
private:
	bool value;
};

class i8_t : public ir_type{
public:
	i8_t(bool var_sign, uint8_t val) : ir_type(){
		sign = var_sign;
		value = val;
	}
	~i8_t(){}
	bool is_signed() override{ return sign; }
	bool is_possible_string() override {return true;}
	void print() override{
			// std::cout << "i8 " << (uint16_t)value;
			std::cout << (uint16_t)value << " ";
			// if (value != 0){
				// std::cout << (uint16_t)value << " ";
			// }
	}

private:
	bool sign;
	uint8_t value;
};

class i16_t : public ir_type{
public:
	i16_t(bool var_sign, uint16_t val) : ir_type(){
		sign = var_sign;
		value = val;
	}
	~i16_t(){}
	bool is_signed() override{ return sign; }
	void print() override{
		// std::cout << "i16 " << value;
			std::cout << value << " ";
			// if (value != 0){
				// std::cout << value << " ";
			// }
	}

private:
	bool sign;
	uint16_t value;

};

class i32_t : public ir_type{
public:
	i32_t(bool var_sign, uint32_t val) : ir_type(){
		sign = var_sign;
		value = val;
	}
	~i32_t(){}
	bool is_signed() override{ return sign; }
	void print() override{
			// std::cout << "i32 " << value;
			std::cout << value << " ";
			// if (value != 0){
				// std::cout << value << " ";
			// }
	}

private:
	bool sign;
	uint32_t value;

};

class i64_t: public ir_type{
public:
	i64_t(bool var_sign, uint64_t val) : ir_type(){
		sign = var_sign;
		value = val;
	}
	~i64_t(){}
	bool is_signed() override{ return sign; }
	void print() override{
			// std::cout << "i64 " << value;
			std::cout << value << " ";
			// if (value != 0){
				// std::cout << value << " ";
			// }
	}

private:
	bool sign;
	uint64_t value;
};

class i128_t: public ir_type{
public:
	i128_t(bool var_sign, __uint128_t val) : ir_type(){
		sign = var_sign;
		value = val;
	}
	~i128_t(){}
	bool is_signed() override{ return sign; }
	void print() override{
			// std::string t = std::to_string(value);
			std::string str_value = "";
			__uint128_t mod = 10;
			__uint128_t temp_value = value;
			do{
				str_value.push_back((unsigned int) (temp_value % mod));
				temp_value = temp_value / 10;
			}while(temp_value != 0);

			std::reverse(str_value.rbegin(), str_value.rend());
			// std::cout << "i128 " << str_value;
			std::cout << str_value << " ";
	}

private:
	bool sign;
	__uint128_t value;
};

class float_t : public ir_type{
public:
	float_t(float val) : ir_type(){
		value = val;
	}
	~float_t(){}
	bool is_signed() override{ return true; }
	void print() override{ std::cout << value << " "; }

private:
	float value;

};

class double_t : public ir_type{
public:
	double_t(double val) : ir_type(){
		value = val;
	}
	~double_t(){}
	bool is_signed() override{ return true; }
	void print() override{	std::cout << value << " "; }

private:
	double value;

};

class exception : public ir_type{
public:
	exception() : ir_type(){}
	~exception(){}
	// void print() override{std::cout << "Exception ";}
	void print() override{return;}
private:
};

class undefined : public ir_type{
public:
	undefined(const char* t_n) : ir_type(){
		type_name = t_n;
	}
	~undefined(){}
	bool is_undefined() override{
		return true;
	}
	void print() override{
		// std::cout << "Undefined '" << type_name << "' ";
		return;
	}
private:
	const char* type_name;
};

class unallocated : public ir_type{
public:
	unallocated() : ir_type(){}
	void print() override{
		// std::cout << "nullptr ";
	}
private:

};

class ptr_t : public ir_type{
public:
	ptr_t(uint64_t addr) : ir_type(){
		value = nullptr;
		address = addr;

		if (address == 0){
			value = new unallocated();
		}
	}
	~ptr_t(){
		delete value;
	}
	bool is_signed() override{ return value->is_signed(); }
	bool is_terminal() override{ return false; }
	bool is_undefined() override{
		return value->is_undefined();
	}
	bool is_updated() override {
		if (value == nullptr){
			return false;
		}else{
			return value->is_updated();
		}
	}
	void represent_as_string() override{
		if (address != 0){
			const char *t = (const char*)address;
			string_array = t;
			show_as_string = true;
		}
		return;
	}

	void print() override{

		// std::cout << "Pointer with address: " << address << " to ";
		if (value == nullptr){
			assert("Value of ptr is null, but shouldnt.");
		}else if (value->is_possible_string() ){// && show_as_string){  //this else if is not useless: A string is an i8*. If you don't treat it like one you will miss the next bytes
			strip_chars(string_array);
			represent_as_string();
			for (unsigned c = 0; c < string_array.size(); c++){
				std::cout << unsigned(string_array[c]) << " ";
			}
			// std::cout << "str \"" << string_array << "\" ";
			// std::cout << string_array << " ";
		}else{
			// std::cout << "address: " << address <<  " *";
			// std::cout << " *";
			value->print();
		}
	}
	void push(ir_type* t) override{

		if (value == nullptr){
			value = t;
		}else{
			value->push(t);
		}
	}

private:
	ir_type *value;
	std::string string_array; //handle this with extra caution
	bool show_as_string = false;
	uint64_t address;

};

class array_t : public ir_type{
public:
	array_t(uint64_t s) : ir_type(){
		array_size = s;
		updated_array = false;
		index = 0;
		arr_elements = new ir_type*[array_size];
		for (unsigned i = 0; i < array_size; i++){
			arr_elements[i] = nullptr;
		}
		// is_term_type = true;
	}
	~array_t(){
		for (unsigned i = 0; i < array_size; i++){
			delete arr_elements[i];
		}
		delete [] arr_elements;
	}
	bool is_terminal() override{ return false; }
	bool is_undefined() override{
		return (updated_array ? arr_elements[array_size - 1]->is_undefined() : true);
	}
	bool is_updated() override{
		if (arr_elements[array_size - 1] == nullptr){
			return false;
		}else{
			return arr_elements[array_size - 1]->is_updated();
		}
	}
	void push(ir_type* t) override{

		if (index >= array_size){
			assert("Index surpassed size!");
		}
		if (arr_elements[index] == nullptr){
			arr_elements[index] = t;
		}else{
			arr_elements[index]->push(t);
		}
		index = ( arr_elements[index]->is_updated() ? index + 1 : index);
		updated_array = (index == array_size ? true : false);
	}
	void print() override{

		if (!updated_array){
			assert("Array is not full, but should be.");
		}else{
			// std::cout << "Array of size: " << array_size << " and type: ";
			// std::cout << "Array " << array_size << " elements ";
			for (unsigned i = 0; i < array_size; i++){
				arr_elements[i]->print();
				// std::cout << ", ";
			}
		}
	}

private:
	uint64_t array_size;
	ir_type **arr_elements;
	bool updated_array;
	unsigned index;
};

class struct_t : public ir_type{
public:
	struct_t(const char *n, uint64_t s) : ir_type(){
		struct_name = n;
		struct_size = s;
		index = 0;
		updated_struct = false;
		if (struct_size > 0){
			struct_elements = new ir_type*[struct_size];
		}
		for (unsigned i = 0; i < struct_size; i++){
			struct_elements[i] = nullptr;
		}
	}
	~struct_t(){
		for (unsigned i = 0; i < struct_size; i++){
			delete struct_elements[i];
		}
		delete [] struct_elements;
	}
	bool is_terminal() override {	return false; }
	bool is_updated() override {
		return ( struct_size != 0 ? ( (struct_elements[struct_size - 1] == nullptr) ? false
																					: struct_elements[struct_size - 1]->is_updated() )
								: true);
	}
	void push(ir_type *t) override{
		if (index >= struct_size){
			assert("Index surpassed size!");
		}
		//----dummy string initialization on struct. Will be removed on generic impl
		// This line actually instructs the struct member, if it is a pointer, to represent its item as a string.
		// This will happen only if the pointer points to an i8. So all in all, if the t = i8*, it will be printed as string
		// t->represent_as_string();
		//
		if (struct_elements[index] == nullptr){
			struct_elements[index] = t;
		}else{
			struct_elements[index]->push(t);
		}
		index = ( struct_elements[index]->is_updated() ? index + 1 : index);
		updated_struct = (index == struct_size ? true : false);
	}
	void print() override{
		// if (!updated_struct){
		// 	assert("Struct is not fully updated, but should be");
		// }else{
		// 	std::cout << "Struct " << struct_name << " " << struct_size << " elements: ";
		// 	for (unsigned i = 0; i < struct_size; i++){
		// 		struct_elements[i]->print();
		// 		// std::cout << ", ";
		// 	}
		// }
	

		// std::cout << "Struct " << struct_name << " " << index << " elements: ";
		for (unsigned i = 0; i < index; i++){
			struct_elements[i]->print();
			// std::cout << ", ";
		}


	}
private:
	const char* struct_name;
	uint64_t struct_size;
	ir_type **struct_elements;
	unsigned index;
	bool updated_struct;
};
