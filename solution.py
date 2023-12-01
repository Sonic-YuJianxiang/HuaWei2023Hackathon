# python solution.py
# required version: python 11.0

import time
import os
import math

for file in os.listdir('testcases'):
    # filename = 'testcases/'+file
    filename = "toy_example_final.txt"


    # read file
    slice_info = []
    strategy = None    # 0: BBB, 1: CBB, 2: CCB, 3: CCC
    cloud_cost_arr = None
    bbu_cost_arr = None
    io_cost_arr = None

    with open(filename, 'r') as f:
        lines = f.readlines()

        baseline_cost, frozen_period, min_bandwidth, penalty = [int(x) for x in lines[0].split()]
        cloud_cpu_cost, cloud_mem_cost = [int(x) for x in lines[1].split()]
        bbu_b, bbu_cpu, bbu_mem, bbu_acc, bbu_cost = [int(x) for x in lines[2].split()]
        slices_num, time_horizon, cpu_acc_ratio = [int(x) for x in lines[3].split()]

        for i in range(slices_num):
            tmp = []
            for j in range(5):
                tmp.append([int(x) for x in lines[i*5+4+j].split()])
            slice_info.append(tmp)
        
        strategy = [[0 for _ in range(time_horizon)] for _ in range(slices_num)]    # 0: BBB, 1: CBB, 2: CCB, 3: CCC

        cloud_cost_arr = [0 for _ in range(time_horizon)]
        bbu_cost_arr = [0 for _ in range(time_horizon)]
        io_cost_arr = [0 for _ in range(time_horizon)]

    
    # schedule

    start = time.time()
    for t in range(time_horizon):
        cnt_cpu, cnt_mem, cnt_acc = 0, 0, 0
        for s in range(slices_num):
            cpu_tmp = slice_info[s][0][0] + slice_info[s][1][0] + slice_info[s][2][0]
            mem_tmp = slice_info[s][0][1] + slice_info[s][1][1] + slice_info[s][2][1]
            acc_tmp = slice_info[s][0][2] + slice_info[s][1][2] + slice_info[s][2][2]

            feasible = False
            if not feasible:
                cnt_cpu += slice_info[s][-1][t] * cpu_tmp
                cnt_mem += slice_info[s][-1][t] * mem_tmp
                cnt_acc += slice_info[s][-1][t] * acc_tmp

                bbu_num = max(max(cnt_cpu / bbu_cpu, cnt_mem / bbu_mem), cnt_acc / bbu_acc)
                if bbu_num > bbu_b:
                    cnt_cpu -= slice_info[s][-1][t] * cpu_tmp
                    cnt_mem -= slice_info[s][-1][t] * mem_tmp
                    cnt_acc -= slice_info[s][-1][t] * acc_tmp
                else:
                    feasible = True
                    strategy[s][t] = 0
                    io_cost_arr[t] += slice_info[s][-1][t] * slice_info[s][-2][0]

            if not feasible:
                tmp1 = cpu_tmp - slice_info[s][0][0]
                tmp2 = mem_tmp - slice_info[s][0][1]
                tmp3 = acc_tmp - slice_info[s][0][2]

                cnt_cpu += slice_info[s][4][t] * tmp1
                cnt_mem += slice_info[s][4][t] * tmp2
                cnt_acc += slice_info[s][4][t] * tmp3

                bbu_num = max(max(cnt_cpu / bbu_cpu, cnt_mem / bbu_mem), cnt_acc / bbu_acc)
                if bbu_num > bbu_b:
                    cnt_cpu -= slice_info[s][4][t] * tmp1
                    cnt_mem -= slice_info[s][4][t] * tmp2
                    cnt_acc -= slice_info[s][4][t] * tmp3
                else:
                    feasible = True
                    strategy[s][t] = 1
                    io_cost_arr[t] += slice_info[s][4][t] * slice_info[s][3][1]
                    cloud_cost_arr[t] += ((cpu_tmp-tmp1) + (acc_tmp-tmp3) * cpu_acc_ratio) * cloud_cpu_cost * slice_info[s][4][t] + (mem_tmp-tmp2) * cloud_mem_cost * slice_info[s][4][t]

            if not feasible:
                tmp1 = slice_info[s][2][0]
                tmp2 = slice_info[s][2][1]
                tmp3 = slice_info[s][2][2]

                cnt_cpu += slice_info[s][4][t] * tmp1
                cnt_mem += slice_info[s][4][t] * tmp2
                cnt_acc += slice_info[s][4][t] * tmp3

                bbu_num = max(max(cnt_cpu / bbu_cpu, cnt_mem / bbu_mem), cnt_acc / bbu_acc)
                if bbu_num > bbu_b:
                    cnt_cpu -= slice_info[s][4][t] * tmp1
                    cnt_mem -= slice_info[s][4][t] * tmp2
                    cnt_acc -= slice_info[s][4][t] * tmp3
                else:
                    feasible = True
                    strategy[s][t] = 2
                    io_cost_arr[t] += slice_info[s][4][t] * slice_info[s][3][2]
                    cloud_cost_arr[t] += ((cpu_tmp-tmp1) + (acc_tmp-tmp3) * cpu_acc_ratio) * cloud_cpu_cost * slice_info[s][4][t] + (mem_tmp-tmp2) * cloud_mem_cost * slice_info[s][4][t]



            if not feasible:
                strategy[s][t] = 3
                io_cost_arr[t] += slice_info[s][-1][t] * slice_info[s][-2][-1]
                cloud_cost_arr[t] += (cpu_tmp + acc_tmp * cpu_acc_ratio) * cloud_cpu_cost * slice_info[s][-1][t] + mem_tmp * cloud_mem_cost * slice_info[s][-1][t]
                feasible = True

        bbu_num = math.ceil(max(max(cnt_cpu / bbu_cpu, cnt_mem / bbu_mem), cnt_acc / bbu_acc))

        if bbu_num > bbu_b:
            print("-------------------Invalid solution-------------------")
            break

        bbu_cost_arr[t] = bbu_num * bbu_cost

        if io_cost_arr[t] >= min_bandwidth:
            io_cost_arr[t] += (io_cost_arr[t] - min_bandwidth) * penalty

        # if t != 0:
        #     cnt = 0
        #     for s in range(slices_num):
        #         if strategy[s][t] != strategy[s][t-1]:
        #             cnt += 1
        #     switch_action_cost_arr[t] = cnt * action_cost * 3

    end = time.time()

    print(cloud_cost_arr)
    print(bbu_cost_arr)
    print(io_cost_arr)
    # print(cnt_cpu, cnt_mem, cnt_acc)
    print(strategy)


    # write file
    file_id = file.split('.')[0].split('e')[-1]
    output_file = "output/"+file_id+".csv"
    with open(output_file, 'w') as f:

        for s in range(slices_num):
            line = []
            for t in range(time_horizon):
                if strategy[s][t] == 0:
                    line.append("BBB")
                else:
                    line.append("CCC")
            f.writelines(" ".join(line))
            f.writelines("\n")

        opex = 0
        for t in range(time_horizon):
            opex += cloud_cost_arr[t]
            opex += bbu_cost_arr[t]
            opex += io_cost_arr[t]
        print("opex:", opex)

        score = max(0, baseline_cost / opex - 1)
        print("score:", score)

        exec_time = int((end-start) * 1000)
        print("time:", exec_time)

        cloud_cost_arr = [str(x) for x in cloud_cost_arr]
        bbu_cost_arr = [str(x) for x in bbu_cost_arr]
        io_cost_arr = [str(x) for x in io_cost_arr]

        f.writelines(" ".join(cloud_cost_arr))
        f.writelines("\n")
        f.writelines(" ".join(bbu_cost_arr))
        f.writelines("\n")
        f.writelines(" ".join(io_cost_arr))
        f.writelines("\n")
        f.writelines(str(opex))
        f.writelines("\n")
        f.writelines(str(score))
        f.writelines("\n")
        f.writelines(str(exec_time))



