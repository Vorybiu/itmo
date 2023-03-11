section data:
	hello: 'Hello World!',0
	i_char: hello

section text:

_start:
	ld $i_char
	cmp #0
	je end
	st OUT
	ld i_char
	add #1
	st i_char
	jmp _start


end:
	hlt