
# Check that the checksum is worked out correctly
# Should be "C8"
#
# The checksum is equal to the sum of all the data bytes of the transmitted file, modulo 256 (8 bits) and then two's complemented. 
# The checking of the checksum is very simple : 
# The sum of the data bytes from the file and the checksum received modulo 256 shall be equal to zero. 
#

proposals = """FC EM 1171_K7NHV 5003 2458 0
FC EM 1173_K7NHV 275 236 0
FC EM 1174_K7NHV 536 406 0
FC EM 1178_K7NHV 8040 3392 0
FC EM 1176_K7NHV 9985 3719 0""".split("\n")

# Add the 
cs = 0
for p in proposals:
    for i in p:
        cs += ord(i)
    cs += ord("\r")


