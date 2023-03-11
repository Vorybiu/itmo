section data:
section text:
_start:
	ld IN
	cmp #0
	JE end
	st OUT
	jmp _start

end:
	hlt