/*
	exhal / inhal (de)compression routines

	This code is released under the terms of the MIT license.
	See COPYING.txt for details.
	
	Copyright (c) 2013-2015 Devin Acker

	Permission is hereby granted, free of charge, to any person obtaining a copy
	of this software and associated documentation files (the "Software"), to deal
	in the Software without restriction, including without limitation the rights
	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the Software is
	furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in
	all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
	THE SOFTWARE.
	
*/

#include <stdio.h>
#include <string.h>
#include "compress.h"
#include "uthash.h"

#ifdef DEBUG_OUT
#define debug(...) printf(__VA_ARGS__)
#else
#define debug(...)
#endif

// compression method values for backref_t and rle_t
typedef enum {
	rle_8   = 0,
	rle_16  = 1,
	rle_seq = 2,

	lz_norm = 0,
	lz_rot  = 1,
	lz_rev  = 2
} method_e;

// used to store and compare backref candidates
typedef struct {
	uint16_t offset, size;
	method_e method;
} backref_t;

// used to store RLE candidates
typedef struct {
	uint16_t size, data;
	method_e method;
} rle_t;

// used to hash and index byte tuples
typedef struct {
	int      bytes;
	uint16_t offset;
	UT_hash_handle hh;
} tuple_t;
// turn 4 bytes into a single integer for quicker hashing/searching
#define COMBINE(w, x, y, z) ((w << 24) | (x << 16) | (y << 8) | z)

uint8_t    rotate (uint8_t);
rle_t      rle_check (uint8_t*, uint8_t*, uint32_t, int);
backref_t  ref_search (uint8_t*, uint8_t*, uint32_t, tuple_t*, int);
uint16_t   write_backref (uint8_t*, uint16_t, backref_t);
uint16_t   write_rle (uint8_t*, uint16_t, rle_t);
uint16_t   write_raw (uint8_t*, uint16_t, uint8_t*, uint16_t);
void       free_offsets(tuple_t*);

// Compresses a file of up to 64 kb.
// unpacked/packed are 65536 byte buffers to read/from write to, 
// inputsize is the length of the uncompressed data.
// Returns the size of the compressed data in bytes, or 0 if compression failed.
size_t pack(uint8_t *unpacked, size_t inputsize, uint8_t *packed, int fast) {
	if (inputsize > DATA_SIZE) return 0;

	// current input/output positions
	uint32_t  inpos = 0;
	uint32_t  outpos = 0;

	// backref and RLE compression candidates
	backref_t backref;
	rle_t     rle;
	
	// used to collect data which should be written uncompressed
	uint8_t  dontpack[LONG_RUN_SIZE];
	uint16_t dontpacksize = 0;

	// index of first locations of byte-tuples used to speed up LZ string search
	tuple_t *offsets = NULL;
	
	debug("inputsize = %d\n", inputsize);
	
	for (uint16_t i = 0; inputsize >= 4 && i < inputsize - 4; i++) {
		tuple_t *tuple;
		int currbytes = COMBINE(unpacked[i], unpacked[i+1], unpacked[i+2], unpacked[i+3]);
		
		// has this one been indexed already
		HASH_FIND_INT(offsets, &currbytes, tuple);
		if (!tuple) {
			tuple = (tuple_t*)malloc(sizeof(tuple_t));
			tuple->bytes = currbytes;
			tuple->offset = i;
			HASH_ADD_INT(offsets, bytes, tuple);
		}
	}
	
	while (inpos < inputsize) {
		// check for a potential RLE
		rle = rle_check(unpacked, unpacked + inpos, inputsize, fast);
		// check for a potential back reference
		if (rle.size < LONG_RUN_SIZE && inputsize >= 3 && inpos < inputsize - 3)
			backref = ref_search(unpacked, unpacked + inpos, inputsize, offsets, fast);
		else backref.size = 0;
		
		// if the backref is a better candidate, use it
		if (backref.size > 3 && backref.size > rle.size) {
			if (outpos + dontpacksize + backref.size >= DATA_SIZE) {
				free_offsets(offsets);
				return 0;
			}
		
			// flush the raw data buffer first
			outpos += write_raw(packed, outpos, dontpack, dontpacksize);
			dontpacksize = 0;
			
			outpos += write_backref(packed, outpos, backref);
			inpos += backref.size;
		}
		// or if the RLE is a better candidate, use it instead
		else if (rle.size >= 2) {
			if (outpos + dontpacksize + rle.size >= DATA_SIZE) {
				free_offsets(offsets);
				return 0;
			}
		
			// flush the raw data buffer first
			outpos += write_raw(packed, outpos, dontpack, dontpacksize);
			dontpacksize = 0;
			
			outpos += write_rle(packed, outpos, rle);
			inpos += rle.size;
			
		}
		// otherwise, write this byte uncompressed
		else {
			dontpack[dontpacksize++] = unpacked[inpos++];
			
			if (outpos + dontpacksize >= DATA_SIZE) {
				free_offsets(offsets);
				return 0;
			}
			
			// if the raw data buffer is full, flush it
			if (dontpacksize == LONG_RUN_SIZE) {
				outpos += write_raw(packed, outpos, dontpack, dontpacksize);
				dontpacksize = 0;
			}
		}
	}
	
	// flush any remaining uncompressed data
	if (outpos + dontpacksize + 1 > DATA_SIZE) {
		free_offsets(offsets);
		return 0;
	}
	
	outpos += write_raw(packed, outpos, dontpack, dontpacksize);
	
	//add the terminating byte
	packed[outpos++] = 0xFF;
	
	free_offsets(offsets);
	return (size_t)outpos;
}

void free_offsets(tuple_t *offsets) {
	tuple_t *curr, *temp;
	HASH_ITER(hh, offsets, curr, temp) {
		HASH_DEL(offsets, curr);
		free(curr);
	}
}

// Decompresses a file of up to 64 kb.
// unpacked/packed are 65536 byte buffers to read/from write to, 
// Returns the size of the uncompressed data in bytes or 0 if decompression failed.
size_t unpack(uint8_t *packed, uint8_t *unpacked) {
	// current input/output positions
	uint32_t  inpos = 0;
	uint32_t  outpos = 0;

	uint8_t  input;
	uint16_t command, length, offset;
	int      methoduse[7] = {0};
	
	while (1) {
		// read command byte from input
		input = packed[inpos++];
		
		// command 0xff = end of data
		if (input == 0xFF)
			break;
		
		// check if it is a long or regular command, get the command no. and size
		if ((input & 0xE0) == 0xE0) {
			command = (input >> 2) & 0x07;
			// get LSB of length from next byte
			length = (((input & 0x03) << 8) | packed[inpos++]) + 1;
		} else {
			command = input >> 5;
			length = (input & 0x1F) + 1;
		}
		
		// don't try to decompress > 64kb
		if (((command == 2) && (outpos + 2*length > DATA_SIZE))
			 || (outpos + length > DATA_SIZE)) {
			return 0;
		}
		
		switch (command) {
		// write uncompressed bytes
		// (note: i had to go back to using loops for all of these because memcpy/memmove
		//  were both fucking up and handling these inconsistently between versions of gcc)
		case 0:
			memcpy(&unpacked[outpos], &packed[inpos], length);
			
			outpos += length;
			inpos  += length;
			break;
		
		// 8-bit RLE
		case 1:
			for (int i = 0; i < length; i++)
				unpacked[outpos++] = packed[inpos];

			inpos++;
			break;

		// 16-bit RLE
		case 2:
			for (int i = 0; i < length; i++) {
				unpacked[outpos++] = packed[inpos];
				unpacked[outpos++] = packed[inpos+1];
			}

			inpos += 2;
			break;

		// 8-bit increasing sequence
		case 3:
			for (int i = 0; i < length; i++)
				unpacked[outpos++] = packed[inpos] + i;

			inpos++;
			break;
			
		// regular backref
		// (offset is big-endian)
		case 4:
		case 7:
			// 7 isn't a real method number, but it behaves the same as 4 due to a quirk in how
			// the original decompression routine is programmed. (one of Parasyte's docs confirms
			// this for GB games as well). let's handle it anyway
			command = 4;

			offset = (packed[inpos] << 8) | packed[inpos+1];
			for (int i = 0; i < length; i++)
				unpacked[outpos++] = unpacked[offset + i];

			inpos += 2;
			break;

		// backref with bit rotation
		// (offset is big-endian)
		case 5:
			offset = (packed[inpos] << 8) | packed[inpos+1];
			for (int i = 0; i < length; i++)
				unpacked[outpos++] = rotate(unpacked[offset + i]);

			inpos += 2;
			break;

		// backwards backref
		// (offset is big-endian)
		case 6:
			offset = (packed[inpos] << 8) | packed[inpos+1];
			for (int i = 0; i < length; i++)
				unpacked[outpos++] = unpacked[offset - i];

			inpos += 2;
		}
		
		// keep track of how many times each compression method is used
		methoduse[command]++;
	}

#ifdef EXTRA_OUT
	printf("Method             Uses\n");
	printf("No compression   : %i\n", methoduse[0]);
	printf("RLE (8-bit)      : %i\n", methoduse[1]);
	printf("RLE (16-bit)     : %i\n", methoduse[2]);
	printf("RLE (sequence)   : %i\n", methoduse[3]);
	printf("Backref (normal) : %i\n", methoduse[4]);
	printf("Backref (rotate) : %i\n", methoduse[5]);
	printf("Backref (reverse): %i\n", methoduse[6]);
	
	printf("\nCompressed size:   %u bytes\n", inpos);
#endif

	return (size_t)outpos;
}

// Decompress data from an offset into a file
size_t unpack_from_file (FILE *file, size_t offset, uint8_t *unpacked) {
	uint8_t packed[DATA_SIZE];
	
	fseek(file, offset, SEEK_SET);
	fread((void*)packed, DATA_SIZE, 1, file);
	if (!ferror(file))
		return unpack(packed, unpacked);
		
	return 0;
}

// Reverses the order of bits in a byte.
// One of the back reference methods does this. As far as game data goes, it seems to be
// pretty useful for compressing graphics.
uint8_t rotate (uint8_t i) {
	uint8_t j = 0;
	if (i & 0x01) j |= 0x80;
	if (i & 0x02) j |= 0x40;
	if (i & 0x04) j |= 0x20;
	if (i & 0x08) j |= 0x10;
	if (i & 0x10) j |= 0x08;
	if (i & 0x20) j |= 0x04;
	if (i & 0x40) j |= 0x02;
	if (i & 0x80) j |= 0x01;
	
	return j;
}

// Searches for possible RLE compressed data.
// start and current are positions within the uncompressed input stream.
// fast enables faster compression by ignoring sequence RLE.
rle_t rle_check (uint8_t *start, uint8_t *current, uint32_t insize, int fast) {
	rle_t candidate = { 0, 0, 0 };
	size_t size;
	
	// check for possible 8-bit RLE
	for (size = 0; size <= LONG_RUN_SIZE && current + size < start + insize; size++)
		if (current[size] != current[0]) break;
		
	// if this is better than the current candidate, use it
	if (size > LONG_RUN_SIZE) size = LONG_RUN_SIZE;
	if (size > 2 && size > candidate.size) {
		candidate.size = size;
		candidate.data = current[0];
		candidate.method = rle_8;
		
		debug("\trle_check: found new candidate (size = %d, method = %d)\n", candidate.size, candidate.method);
	}
	
	// check for possible 16-bit RLE
	uint16_t first = current[0] | (current[1] << 8);
	for (size = 0; size <= LONG_RUN_SIZE && current + size < start + insize - 1; size += 2) {
		uint16_t next = current[size] | (current[size + 1] << 8);
		if (next != first) break;
	}
		
	// if this is better than the current candidate, use it
	if (size > LONG_RUN_SIZE) size = LONG_RUN_SIZE;
	if (size > 2 && size > candidate.size) {
		candidate.size = size;
		candidate.data = first;
		candidate.method = rle_16;
		
		debug("\trle_check: found new candidate (size = %d, method = %d)\n", candidate.size, candidate.method);
	}
	
	// fast mode: don't use sequence RLE
	if (fast) return candidate;
	
	// check for possible sequence RLE
	for (size = 0; size <= LONG_RUN_SIZE && current + size < start + insize; size++)
		if (current[size] != (current[0] + size)) break;
		
	// if this is better than the current candidate, use it
	if (size > LONG_RUN_SIZE) size = LONG_RUN_SIZE;
	if (size > 2 && size > candidate.size) {
		candidate.size = size;
		candidate.data = current[0];
		candidate.method = rle_seq;
		
		debug("\trle_check: found new candidate (size = %d, method = %d)\n", candidate.size, candidate.method);
	}
	
	return candidate;
}

// Searches for the best possible back reference.
// start and current are positions within the uncompressed input stream.
// fast enables fast mode which only uses regular forward references
backref_t ref_search (uint8_t *start, uint8_t *current, uint32_t insize, tuple_t *offsets, int fast) {
	backref_t candidate = { 0, 0, 0 };
	uint16_t size;
	int currbytes;
	tuple_t *tuple;
	
	// references to previous data which goes in the same direction
	// see if this byte pair exists elsewhere, then start searching.
	currbytes = COMBINE(current[0], current[1], current[2], current[3]);
	HASH_FIND_INT(offsets, &currbytes, tuple);
	if (tuple) for (uint8_t *pos = start + tuple->offset; pos < current; pos++) {
		// see how many bytes in a row are the same between the current uncompressed data
		// and the data at the position being searched
		for (size = 0; size <= LONG_RUN_SIZE && current + size < start + insize; size++) 
			if (pos[size] != current[size]) break;
			
		// if this is better than the current candidate, use it
		if (size > LONG_RUN_SIZE) size = LONG_RUN_SIZE;
		if (size > 3 && size > candidate.size) {
			candidate.size = size;
			candidate.offset = pos - start;
			candidate.method = lz_norm;
			
			debug("\tref_search: found new candidate (offset: %4x, size: %d, method = %d)\n", candidate.offset, candidate.size, candidate.method);
		}
	}
	
	// fast mode: forward references only
	if (fast) return candidate;
	
	// references to data where the bits are rotated
	// see if this byte pair exists elsewhere, then start searching.
	currbytes = COMBINE(rotate(current[0]), rotate(current[1]), rotate(current[2]), rotate(current[3]));
	HASH_FIND_INT(offsets, &currbytes, tuple);
	if (tuple) for (uint8_t *pos = start + tuple->offset; pos < current; pos++) {	
		// now repeat the check with the bit rotation method
		for (size = 0; size <= LONG_RUN_SIZE && current + size < start + insize; size++) 
			if (pos[size] != rotate(current[size])) break;
				
		// if this is better than the current candidate, use it
		if (size > LONG_RUN_SIZE) size = LONG_RUN_SIZE;
		if (size > 3 && size > candidate.size) {
			candidate.size = size;
			candidate.offset = pos - start;
			candidate.method = lz_rot;
			
			debug("\tref_search: found new candidate (offset: %4x, size: %d, method = %d)\n", candidate.offset, candidate.size, candidate.method);
		}
	}
	
	// references to data which goes backwards
	// see if this byte pair exists elsewhere, then start searching.
	currbytes = COMBINE(current[3], current[2], current[1], current[0]);
	HASH_FIND_INT(offsets, &currbytes, tuple);
	// add 3 to offset since we're starting at the end of the 4 byte sequence here
	if (tuple) for (uint8_t *pos = start + tuple->offset + 3; pos < current; pos++) {
		// now repeat the check but go backwards
		for (size = 0; size <= LONG_RUN_SIZE && current + size < start + insize; size++)
			if (start[pos - start - size] != current[size]) break;
		
		// if this is better than the current candidate, use it
		if (size > LONG_RUN_SIZE) size = LONG_RUN_SIZE;
		if (size > 3 && size > candidate.size) {
			candidate.size = size;
			candidate.offset = pos - start;
			candidate.method = lz_rev;
			
			debug("\tref_search: found new candidate (offset: %4x, size: %d, method = %d)\n", candidate.offset, candidate.size, candidate.method);
		}
	}
	
	return candidate;
}

// Writes a back reference to the compressed output stream.
// Returns number of bytes written
uint16_t write_backref (uint8_t *out, uint16_t outpos, backref_t backref) {
	uint16_t size = backref.size - 1;
	int outsize;
	
	debug("write_backref: writing backref to %4x, size %d (method %d)\n", backref.offset, backref.size, backref.method);
	
	// long run
	if (size >= RUN_SIZE) {
		// write command byte / MSB of size
		out[outpos++] = (0xF0 + (backref.method << 2)) | (size >> 8);
		// write LSB of size
		out[outpos++] = size & 0xFF;
		
		outsize = 4;
	} 
	// normal size run
	else {
		// write command byte / size
		out[outpos++] = (0x80 + (backref.method << 5)) | size;
		outsize = 3;
	}
	
	// write MSB of offset
	out[outpos++] = backref.offset >> 8;
	// write LSB of offset
	out[outpos++] = backref.offset & 0xFF;
	
	return outsize;
}

// Writes RLE data to the compressed output stream.
// Returns number of bytes written
uint16_t write_rle (uint8_t *out, uint16_t outpos, rle_t rle) {
	uint16_t size;
	int outsize;
	
	if (rle.method == rle_16)
		size = (rle.size / 2) - 1;
	else
		size = rle.size - 1;
	
	debug("write_rle: writing %d bytes of data 0x%02x (method %d)\n", rle.size, rle.data, rle.method);
	
	// long run
	if (size >= RUN_SIZE) {
		// write command byte / MSB of size
		out[outpos++] = (0xE4 + (rle.method << 2)) | (size >> 8);
		// write LSB of size
		out[outpos++] = size & 0xFF;
		
		outsize = 3;
	}
	// normal size run
	else {
		// write command byte / size
		out[outpos++] = (0x20 + (rle.method << 5)) | size;
		
		outsize = 2;
	}
	
	out[outpos++] = rle.data;
	// write upper byte of 16-bit RLE (and adjust written data size)
	if (rle.method == rle_16) {
		out[outpos++] = rle.data >> 8;
		outsize++;
	}
	
	return outsize;
}

// Write uncompressed data to the output stream.
// Returns number of bytes written.
uint16_t write_raw (uint8_t *out, uint16_t outpos, uint8_t *in, uint16_t insize) {
	if (!insize) return 0;

#ifdef DEBUG_OUT
	printf("write_raw: writing %d bytes unpacked data: ", insize);
	for (int i = 0; i < insize; i++)
		printf("%02x ", in[i]);
	
	printf("\n");
#endif

	uint16_t size = insize - 1;
	int outsize;
	
	if (size >= RUN_SIZE) {
		// write command byte + MSB of size
		out[outpos++] = 0xE0 + (size >> 8);
		// write LSB of size
		out[outpos++] = size & 0xFF;
		
		outsize = insize + 2;
	}
	// normal size run
	else {
		// write command byte / size
		out[outpos++] = size;
		
		outsize = insize + 1;
	}
	
	// write data
	memcpy(&out[outpos], in, insize);
	
	return outsize;
}
