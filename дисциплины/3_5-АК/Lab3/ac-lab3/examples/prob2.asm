section data:
	result 0;
	first 1;
	second 2;
	even 1;
	max 4000000
	digits 0,0,0,0,0,0,0,0,0
	temp_digit digits


section text:

_start:
	ld second
	and even
	je sum
	jmp next
sum:
	ld result
	add second
	st result
next:
	ld second
	add first
	st second
	sub first
	st first
	ld second
	sub max
	jl _start
	ld temp_digit

	add #1
	st temp_digit

digits_result:
	ld result
	mod #10
	add #'0'
	st $temp_digit
	ld result
	div #10
	cmp #0
	je print_result
	st result
	ld temp_digit
	add #1
	st temp_digit
	jmp digits_result

print_result:
	ld $temp_digit
	cmp #0
	je end
	st OUT
	ld temp_digit
	sub #1
	st temp_digit
	jmp print_result

end:
	hlt
