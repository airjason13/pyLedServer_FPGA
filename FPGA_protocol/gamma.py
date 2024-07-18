import math

max_gamma_value = 24    # gamma 0 ~ gamma 24

# from gamma 0 ~ gamma 24
gamma_table_list = []


def gen_gamma(nsteps, gamma):
    gammaedUp = [math.pow(x, gamma) for x in range(nsteps)]

    return [x/max(gammaedUp) for x in gammaedUp]


def rounder(topValue, gammas):
    return [min(topValue, round(x*topValue)) for x in gammas]


def init_gamma_table_list(gamma_min=0, gamma_max=max_gamma_value+1, gamma_steps=256):
    for i_gamma_tmp in range(gamma_min, gamma_max):
        bytes_test = bytes()
        for value in rounder(255, gen_gamma(gamma_steps, i_gamma_tmp/10)):
            # i_gamma_tmp.append(value)
            # byte_gamma_tmp.append(int(value).to_bytes(4, byteorder='big'))
            bytes_test += int(value).to_bytes(2, byteorder='big')
        gamma_table_list.append(bytes_test)


if __name__ == "__main__":
    # myGamma = 1
    steps = 255

    i_gamma_tmp = []
    byte_gamma_tmp = []
    gamma_table_list = []
    bytes_test = bytes()
    for i in range(0, 24):
        bytes_test = bytes()
        for value in rounder(255, gen_gamma(steps, i/10)):
            # i_gamma_tmp.append(value)
            # byte_gamma_tmp.append(int(value).to_bytes(4, byteorder='big'))
            bytes_test += int(value).to_bytes(4, byteorder='big')
        gamma_table_list.append(bytes_test)
    # print("i_gamma_tmp : ", i_gamma_tmp)
    # print("byte_gamma_tmp : ", byte_gamma_tmp)
    # print("bytes_test : ", bytes_test)
    print("gamma_table_list[0] : ", gamma_table_list[0])
    print("gamma_table_list[12] : ", gamma_table_list[12])

    '''output = open("gamma.h", "w")
    output.write("/* %d-step brightness table: gamma = %s */ \n\n" % (steps, myGamma))
    output.write("const uint8_t gamma_table[%d] = {\n" % steps)
    for value in rounder(255, gamma(steps, myGamma)):
        output.write("\t %d,\n" % value)
    output.write("};\n")
    output.close()'''

