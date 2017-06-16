#include <stdio.h>
#include <string.h>
#include <Python.h>

#define uchar           unsigned char
#define uint            unsigned int

void initBitrevs(uchar* bitrevs) {
	int i;
	uchar *x;
	for (i=0; i<256; ++i) {
		x = &(bitrevs[i]);
		*x = (uchar) i;
		*x = (((*x >> 1) & 0x55) | ((*x << 1) & 0xAA));
		*x = (((*x >> 2) & 0x33) | ((*x << 2) & 0xCC));
		*x = (((*x >> 4) & 0x0F) | ((*x << 4) & 0xF0));
	}
}

void encode(uchar **bpos, int length, int type) {
	if(length > 32) {
		*(*bpos)++ = 0xE0 + 4 * type + ((length - 1) >> 8);
		*(*bpos)++ = (length - 1) & 0xFF;
	} else
	        *(*bpos)++ = 0x20 * type + length - 1;
}

void rencode(uchar **bpos, uchar *pos, int length) {
	if(length <= 0)
		  return;
	encode(bpos, length, 0);
	memcpy(*bpos, pos, length);
	*bpos += length;
}

int comp_(uchar *udata, uchar *buffer, int length) {
        uchar *bpos = buffer, *limit = &udata[length];
        uchar *pos = udata, *pos2, *pos3, *pos4;
        int tmp;
	uchar bitrevs[256];
	initBitrevs(bitrevs);
        while(pos < limit) {
                /*printf("%d\t%d\n", pos - udata, bpos - buffer);*/
                /* Look for patterns */
                for(pos2 = pos; pos2 < limit && pos2 < pos + 1024; pos2++) {

                        for(pos3 = pos2; pos3 < limit && pos3 < pos2 + 1024 && *pos2 == *pos3; pos3++);
                        if(pos3 - pos2 >= 3) {
                                rencode(&bpos, pos, pos2 - pos);
                                encode(&bpos, pos3 - pos2, 1);
                                *bpos++ = *pos2;
                                pos = pos3;
                                break;
                        }
                        
                        for(pos3 = pos2; pos3 < limit && pos3 < pos2 + 2048 && *pos3 == *pos2 && pos3[1] == pos2[1]; pos3 += 2);
                        if(pos3 - pos2 >= 6) {
                                rencode(&bpos, pos, pos2 - pos);
                                encode(&bpos, (pos3 - pos2) / 2, 2);
                                *bpos++ = pos2[0];
                                *bpos++ = pos2[1];
                                pos = pos3;
                                break;
                        }
                        for(tmp = 0, pos3 = pos2; pos3 < limit && pos3 < pos2 + 1024 && *pos3 == *pos2 + tmp; pos3++, tmp++);
                        if(pos3 - pos2 >= 4) {
                                rencode(&bpos, pos, pos2 - pos);
                                encode(&bpos, pos3 - pos2, 3);
                                *bpos++ = *pos2;
                                pos = pos3;
                                break;
                        }

                        for(pos3 = udata; pos3 < pos2; pos3++) {
                                
                                for(tmp = 0, pos4 = pos3; pos4 < pos2 && tmp < 1024 && pos2 + tmp < limit && *pos4 == pos2[tmp]; pos4++, tmp++);
                                if(tmp >= 5) {
                                        rencode(&bpos, pos, pos2 - pos);
                                        encode(&bpos, tmp, 4);
                                        *bpos++ = (pos3 - udata) >> 8;
                                        *bpos++ = (pos3 - udata) & 0xFF;
                                        pos = pos2 + tmp;
                                        goto DONE;
                                }
                                
                                for(tmp = 0, pos4 = pos3; pos4 < pos2 && tmp < 1024 && pos2 + tmp < limit && *pos4 == bitrevs[pos2[tmp]]; pos4++, tmp++);
                                if(tmp >= 5) {
                                        rencode(&bpos, pos, pos2 - pos);
                                        encode(&bpos, tmp, 5);
                                        *bpos++ = (pos3 - udata) >> 8;
                                        *bpos++ = (pos3 - udata) & 0xFF;
                                        pos = pos2 + tmp;
                                        goto DONE;
                                }
                                
                                for(tmp = 0, pos4 = pos3; pos4 >= udata && tmp < 1024 && pos2 + tmp < limit && *pos4 == pos2[tmp]; pos4--, tmp++);
                                if(tmp >= 5) {
                                        rencode(&bpos, pos, pos2 - pos);
                                        encode(&bpos, tmp, 6);
                                        *bpos++ = (pos3 - udata) >> 8;
                                        *bpos++ = (pos3 - udata) & 0xFF;
                                        pos = pos2 + tmp;
                                        goto DONE;
                                }
                        }
                }
                DONE:
                /* Can't compress, so just use 0 (raw) */
                rencode(&bpos, pos, pos2 - pos);
                if(pos < pos2) pos = pos2;
        }
        *bpos++ = 0xFF;
        return bpos - buffer;
}

/* The decompressor function.
 * Takes a pointer to the compressed block, a pointer to the buffer
 * which it decompresses into, . Returns the number of bytes uncompressed,
 * or -1 if decompression failed.
 */
int decomp_(uchar *romBuffer, uint addr, uchar *buffer, int maxlen) {
        uchar *cdata = &romBuffer[addr];
        uchar *bpos = buffer, *bpos2, tmp;
        while(*cdata != 0xFF) {
                int cmdtype = *cdata >> 5;
                int len = (*cdata & 0x1F) + 1;
                if(cmdtype == 7) {
                        cmdtype = (*cdata & 0x1C) >> 2;
                        len = ((*cdata & 3) << 8) + *(cdata + 1) + 1;
                        cdata++;
                }
                if(bpos + len > &buffer[maxlen]) return -1;
                cdata++;
                if(cmdtype >= 4) {
                        bpos2 = &buffer[(*cdata << 8) + *(cdata + 1)];
                        if(bpos2 >= &buffer[maxlen]) return -1;
                        cdata += 2;
                }
                switch(cmdtype) {
                        case 0:
                                memcpy(bpos, cdata, len);
                                cdata += len;
                                bpos += len;
                                break;
                        case 1:
                                memset(bpos, *cdata++, len);
                                bpos += len;
                                break;
                        case 2:
                                if(bpos + 2 * len > &buffer[maxlen]) return -1;
                                while(len--) {
                                        *(short *)bpos = *(short *)cdata;
                                        bpos += 2;
                                }
                                cdata += 2;
                                break;
                        case 3:
                                tmp = *cdata++;
                                while(len--) *bpos++ = tmp++;
                                break;
                        case 4:
                                if(bpos2 + len > &buffer[maxlen]) return -1;
                                memcpy(bpos, bpos2, len);
                                bpos += len;
                                break;
                        case 5:
                                if(bpos2 + len > &buffer[maxlen]) return -1;
                                while(len--) {
                                        tmp = *bpos2++;
                                        tmp = ((tmp >> 1) & 0x55) | ((tmp << 1) & 0xAA);
                                        tmp = ((tmp >> 2) & 0x33) | ((tmp << 2) & 0xCC);
                                        tmp = ((tmp >> 4) & 0x0F) | ((tmp << 4) & 0xF0);
                                        *bpos++ = tmp;
                                }
                                break;
                        case 6:
                                if(bpos2 - len + 1 < buffer) return -1;
                                while(len--) *bpos++ = *bpos2--;
                                break;
                        case 7:
                                return -1;
                }
        }
        return bpos - buffer;
}

static PyObject* comp(PyObject* self, PyObject* args) {
	PyObject *list, *clist, *o;
	int size, i, csize;
	long n;
	uchar *udata, *buffer;

	if (!PyArg_ParseTuple(args, "O", &list))
		return NULL;

	if (!PyList_Check(list))
		return PyErr_Format(PyExc_TypeError, "list of numbers expected ('%s' given)", list->ob_type->tp_name), NULL;

	size = PyList_Size(list);

	if (size < 1)
		return PyErr_Format(PyExc_TypeError, "got empty list"), NULL;

	udata = (uchar*) malloc(sizeof(uchar) * size);

	for (i=0; i<size; ++i) {
		o = PyList_GetItem(list, i);
		if (!PyInt_Check(o)) {
                        free(udata);
			return PyErr_Format(PyExc_TypeError, "list of ints expected ('%s') given", o->ob_type->tp_name), NULL;
                }
                n = PyInt_AsLong(o);
		if (n == -1 && PyErr_Occurred()) {
                        free(udata);
			return NULL;
                }
		if (n < 0) {
                        free(udata);
			return PyErr_Format(PyExc_TypeError, "list of positive ints expected (negative found)"), NULL;
                }
                udata[i] = (uchar) n;
	}

	// Allocate a buffer
	buffer = (uchar*) malloc(sizeof(uchar) * (size + 1));
	csize = comp_(udata, buffer, size);
	free(udata);

	clist = PyList_New(csize);
	for (i=0; i<csize; ++i) {
		o = PyInt_FromLong((long) buffer[i]);
		PyList_SetItem(clist, i, o);
	}
	free(buffer);
	return clist;
}

// Given a reference to a Block object, returns a PyByteArray containing its data
// Caches the data from the most recent Block object passed in in order to reduce allocations and marshalling costs
PyObject* get_rom_bytes(PyObject* rom) {
        static PyObject *s_cachedRomArr, *s_cachedRomByteArr;
        PyObject *romArr, *romByteArr;
        int size;

	romArr = PyObject_GetAttr(rom, PyString_FromString("data"));
        if (!romArr)
                return NULL;
        
        // If rom.data array reference hasn't changed, return the cached byte buffer
        if (romArr == s_cachedRomArr) {
                Py_DECREF(romArr);
                return s_cachedRomByteArr;
        }

	romByteArr = PyByteArray_FromObject(romArr);
        if (!romByteArr)
                return NULL;

        if (!PyByteArray_Check(romByteArr))
                return PyErr_Format(PyExc_TypeError, "bytearray of numbers expected ('%s') given", romArr->ob_type->tp_name);

        size = PyByteArray_Size(romByteArr);

        if (size < 1)
                return PyErr_Format(PyExc_TypeError, "rom's data attribute was empty");

        // We are replacing the cached references, so release them before we do
        Py_XDECREF(s_cachedRomArr);
        Py_XDECREF(s_cachedRomByteArr);
        
        // Because this reference to the array is cached, there will always be an extra reference
        // to the rom's data until the program ends
        s_cachedRomArr = romArr;
        s_cachedRomByteArr = romByteArr;
        
        return romByteArr;
}

static PyObject* decomp(PyObject* self, PyObject* args) {
        PyObject *rom, *ulist, *o, *romByteArr;
	int addr, new_size, i;
	uchar *romBuffer, *buffer;

        if (!PyArg_ParseTuple(args, "Oi", &rom, &addr))
                return NULL;

        romByteArr = get_rom_bytes(rom);
        if (!romByteArr)
                return NULL;

        romBuffer = (uchar*) PyByteArray_AS_STRING(romByteArr);

        // Allocate a buffer
        buffer = (uchar*) malloc(sizeof(uchar) * 65536);
        new_size = decomp_(romBuffer, addr, buffer, 65536);

        ulist = PyList_New(new_size);
        for (i=0; i<new_size; ++i) {
                o = PyInt_FromLong((long) buffer[i]);
                PyList_SetItem(ulist, i, o);
        }
        free(buffer);
        return ulist;
}

static PyMethodDef native_compMethods[] = {
	{"comp", comp, METH_VARARGS, "C implementation of EB's comp()"},
	{"decomp", decomp, METH_VARARGS, "C implementation of EB's decomp()"},
	{NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initnative_comp(void)
{
	(void) Py_InitModule("native_comp", native_compMethods);
}
