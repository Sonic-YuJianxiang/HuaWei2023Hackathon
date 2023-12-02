# python solution.py
# required version: python 11.0

import time
import os
import math

def compute_bbu_sets(cpu2bbu, men2bbu, acc2bbu):
    return max(math.ceil(cpu2bbu / bbu_cpu), 
               math.ceil(men2bbu / bbu_mem), 
               math.ceil(acc2bbu / bbu_acc))

res = 0
for file in os.listdir('testcases'):
    filename = 'testcases/'+file

    slice_info = []
    strategy = None    # 0: BBB, 1: CBB, 2: CCB, 3: CCC
    
    # Read file
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
    # switch_action_cost_arr = [0 for _ in range(time_horizon)]


    # schedule
    time_state = [[0 for _ in range(3)] for _ in range(slices_num)]
    prev_state = [None for _ in range(slices_num)]
    start = time.time()
    for t in range(time_horizon):
        cpu2bbu, men2bbu, acc2bbu = 0, 0, 0
        if t == 0:
            for s in range(slices_num):
                # 每个slice在每个时段的Base requirement for cpu, mem, acc
                required_cpu_basic = (slice_info[s][0][0] + slice_info[s][1][0] + slice_info[s][2][0]) * slice_info[s][-1][t]
                required_mem_basic = (slice_info[s][0][1] + slice_info[s][1][1] + slice_info[s][2][1]) * slice_info[s][-1][t]
                required_acc_basic = (slice_info[s][0][2] + slice_info[s][1][2] + slice_info[s][2][2]) * slice_info[s][-1][t]

                # 判断各方案是否可�?
                feasible = False
                
                # 尽量部署到bbu
                cpu2bbu += required_cpu_basic   
                men2bbu += required_mem_basic
                acc2bbu += required_acc_basic
                
                bbu_sets = compute_bbu_sets(cpu2bbu, men2bbu, acc2bbu)
                
                if bbu_sets <= bbu_b:
                    strategy[s][t] = 0  # BBB
                    prev_state[s] = 0
                    feasible = True # BBB方案可行
                    io_cost_arr[t] += slice_info[s][-1][t] * slice_info[s][-2][0]   # Traffic * L_A
                    # bbu_cost_arr[t] += bbu_sets * bbu_cost    
                    bbu_cost_arr[t] = bbu_sets * bbu_cost
                else:
                    # 将预分配到bbu上的资源清零
                    cpu2bbu -= required_cpu_basic   
                    men2bbu -= required_mem_basic
                    acc2bbu -= required_acc_basic
                    
                if not feasible:   # 尝试CBB
                    cpu2bbu += (slice_info[s][1][0] + slice_info[s][2][0]) * slice_info[s][-1][t]
                    men2bbu += (slice_info[s][1][1] + slice_info[s][2][1]) * slice_info[s][-1][t]
                    acc2bbu += (slice_info[s][1][2] + slice_info[s][2][2]) * slice_info[s][-1][t]
                    
                    bbu_sets = compute_bbu_sets(cpu2bbu, men2bbu, acc2bbu)
                    
                    if bbu_sets <= bbu_b:
                        strategy[s][t] = 1  # CBB
                        prev_state[s] = 1
                        feasible = True # CBB方案可行
                        bbu_cost_arr[t] = bbu_sets * bbu_cost
                        io_cost_arr[t] += slice_info[s][-1][t] * slice_info[s][-2][1]   # Traffic * L_B
                        cpu2cloud = slice_info[s][0][0] * slice_info[s][-1][t]
                        mem2cloud = slice_info[s][0][1] * slice_info[s][-1][t]
                        acc2cloud = slice_info[s][0][2] * slice_info[s][-1][t]
                        cloud_cost_arr[t] += (cpu2cloud + acc2cloud * cpu_acc_ratio) * cloud_cpu_cost + mem2cloud * cloud_mem_cost
                    else:
                        cpu2bbu -= (slice_info[s][1][0] + slice_info[s][2][0]) * slice_info[s][-1][t]
                        men2bbu -= (slice_info[s][1][1] + slice_info[s][2][1]) * slice_info[s][-1][t]
                        acc2bbu -= (slice_info[s][1][2] + slice_info[s][2][2]) * slice_info[s][-1][t]
                        
                if not feasible:   # 尝试CCB
                    cpu2bbu += slice_info[s][2][0] * slice_info[s][-1][t]
                    men2bbu += slice_info[s][2][1] * slice_info[s][-1][t]
                    acc2bbu += slice_info[s][2][2] * slice_info[s][-1][t]
                    
                    bbu_sets = compute_bbu_sets(cpu2bbu, men2bbu, acc2bbu)
                    
                    if bbu_sets <= bbu_b:
                        strategy[s][t] = 2  # CCB
                        prev_state[s] = 2
                        feasible = True # CCB方案可行
                        bbu_cost_arr[t] = bbu_sets * bbu_cost
                        io_cost_arr[t] += slice_info[s][-1][t] * slice_info[s][-2][2]   # Traffic * L_C
                        cpu2cloud = (slice_info[s][0][0] + slice_info[s][1][0]) * slice_info[s][-1][t]
                        mem2cloud = (slice_info[s][0][1] + slice_info[s][1][1]) * slice_info[s][-1][t]
                        acc2cloud = (slice_info[s][0][2] + slice_info[s][1][2]) * slice_info[s][-1][t]
                        cloud_cost_arr[t] += (cpu2cloud + acc2cloud * cpu_acc_ratio) * cloud_cpu_cost + mem2cloud * cloud_mem_cost
                    else:
                        cpu2bbu -= slice_info[s][2][0] * slice_info[s][-1][t]
                        men2bbu -= slice_info[s][2][1] * slice_info[s][-1][t]          
                        acc2bbu -= slice_info[s][2][2] * slice_info[s][-1][t]          
                    
                if not feasible:   # 尝试CCC
                    strategy[s][t] = 3 # CCC
                    prev_state[s] = 3
                    io_cost_arr[t] += slice_info[s][-1][t] * slice_info[s][-2][3]  # Traffic * L_D
                    cloud_cost_arr[t] += (required_cpu_basic + required_acc_basic * cpu_acc_ratio) * cloud_cpu_cost + required_mem_basic * cloud_mem_cost
        else:
            for s in range(slices_num):
                # 每个slice在每个时段的Base requirement for cpu, mem, acc
                required_cpu_basic = (slice_info[s][0][0] + slice_info[s][1][0] + slice_info[s][2][0]) * slice_info[s][-1][t]
                required_mem_basic = (slice_info[s][0][1] + slice_info[s][1][1] + slice_info[s][2][1]) * slice_info[s][-1][t]
                required_acc_basic = (slice_info[s][0][2] + slice_info[s][1][2] + slice_info[s][2][2]) * slice_info[s][-1][t]

                # 判断各方案是否可�?
                feasible = False
                time_state_changeble = False

                if prev_state[s] == 0:
                    time_state_changeble = True
                elif prev_state[s] == 1:
                    time_state_changeble = (time_state[s][0] == 0)  # CU剩余冷却时间==0
                elif prev_state[s] == 2:
                    time_state_changeble = ((time_state[s][0] == 0) and (time_state[s][1] == 0))
                elif prev_state[s] == 3:
                    time_state_changeble = ((time_state[s][0] == 0) and (time_state[s][1] == 0) and (time_state[s][2] == 0))

                if time_state_changeble == True:
                    # 尽量部署到bbu
                    cpu2bbu += required_cpu_basic   
                    men2bbu += required_mem_basic
                    acc2bbu += required_acc_basic
                    
                    bbu_sets = compute_bbu_sets(cpu2bbu, men2bbu, acc2bbu)
                    
                    if bbu_sets <= bbu_b:
                        strategy[s][t] = 0  # BBB
                        prev_state[s] = 0
                        feasible = True # BBB方案可行
                        io_cost_arr[t] += slice_info[s][-1][t] * slice_info[s][-2][0]   # Traffic * L_A  
                        bbu_cost_arr[t] = bbu_sets * bbu_cost

                        if prev_state[s] == 0:
                            time_state[s] = [max(0, time_state[s][0]-1),max(0, time_state[s][1]-1), max(0, time_state[s][2]-1)]
                        elif prev_state[s] == 1:
                            time_state[s] = [frozen_period, max(0, time_state[s][1]-1), max(0, time_state[s][2]-1)]
                        elif prev_state[s] == 2:
                            time_state[s] = [frozen_period, frozen_period, max(0, time_state[s][2]-1)]
                        elif prev_state[s] == 3:
                            time_state[s] = [frozen_period, frozen_period, frozen_period]
                    else:
                        # 将预分配到bbu上的资源清零
                        cpu2bbu -= required_cpu_basic   
                        men2bbu -= required_mem_basic
                        acc2bbu -= required_acc_basic

                if not feasible:   # 尝试CBB
                    time_state_changeble = False

                    if prev_state[s] == 0:
                        time_state_changeble = (time_state[s][0] == 0)  # CU剩余冷却时间==0
                    elif prev_state[s] == 1:
                        time_state_changeble = True
                    elif prev_state[s] == 2:
                        time_state_changeble = ((time_state[s][1] == 0))
                    elif prev_state[s] == 3:
                        time_state_changeble = ((time_state[s][1] == 0) and (time_state[s][2] == 0))

                    if time_state_changeble == True:
                        cpu2bbu += (slice_info[s][1][0] + slice_info[s][2][0]) * slice_info[s][-1][t]
                        men2bbu += (slice_info[s][1][1] + slice_info[s][2][1]) * slice_info[s][-1][t]
                        acc2bbu += (slice_info[s][1][2] + slice_info[s][2][2]) * slice_info[s][-1][t]
                        
                        bbu_sets = compute_bbu_sets(cpu2bbu, men2bbu, acc2bbu)
                        
                        if bbu_sets <= bbu_b:
                            strategy[s][t] = 1  # CBB
                            prev_state[s] = 1
                            feasible = True # CBB方案可行
                            bbu_cost_arr[t] = bbu_sets * bbu_cost
                            io_cost_arr[t] += slice_info[s][-1][t] * slice_info[s][-2][1]   # Traffic * L_B
                            cpu2cloud = slice_info[s][0][0] * slice_info[s][-1][t]
                            mem2cloud = slice_info[s][0][1] * slice_info[s][-1][t]
                            acc2cloud = slice_info[s][0][2] * slice_info[s][-1][t]
                            cloud_cost_arr[t] += (cpu2cloud + acc2cloud * cpu_acc_ratio) * cloud_cpu_cost + mem2cloud * cloud_mem_cost

                            if prev_state[s] == 0:
                                time_state[s] = [frozen_period, max(0, time_state[s][1]-1), max(0, time_state[s][2]-1)]
                            elif prev_state[s] == 1:
                                time_state[s] = [max(0, time_state[s][0]-1),max(0, time_state[s][1]-1), max(0, time_state[s][2]-1)]
                            elif prev_state[s] == 2:
                                time_state[s] = [max(0, time_state[s][0]-1), frozen_period, max(0, time_state[s][2]-1)]
                            elif prev_state[s] == 3:
                                time_state[s] = [frozen_period, max(0, time_state[s][1]-1), max(0, time_state[s][2]-1)]
                        else:
                            cpu2bbu -= (slice_info[s][1][0] + slice_info[s][2][0]) * slice_info[s][-1][t]
                            men2bbu -= (slice_info[s][1][1] + slice_info[s][2][1]) * slice_info[s][-1][t]
                            acc2bbu -= (slice_info[s][1][2] + slice_info[s][2][2]) * slice_info[s][-1][t]

                if not feasible:   # 尝试CCB
                    time_state_changeble = False

                    if prev_state[s] == 0:
                        time_state_changeble = ((time_state[s][0] == 0) and (time_state[s][1] == 0))  # CU剩余冷却时间==0
                    elif prev_state[s] == 1:
                        time_state_changeble = (time_state[s][1] == 0)
                    elif prev_state[s] == 2:
                        time_state_changeble = True
                    elif prev_state[s] == 3:
                        time_state_changeble = (time_state[s][2] == 0)

                    if time_state_changeble == True:
                        cpu2bbu += slice_info[s][2][0] * slice_info[s][-1][t]
                        men2bbu += slice_info[s][2][1] * slice_info[s][-1][t]
                        acc2bbu += slice_info[s][2][2] * slice_info[s][-1][t]
                        
                        bbu_sets = compute_bbu_sets(cpu2bbu, men2bbu, acc2bbu)
                        
                        if bbu_sets <= bbu_b:
                            strategy[s][t] = 2  # CCB
                            prev_state[s] = 2
                            feasible = True # CCB方案可行
                            bbu_cost_arr[t] = bbu_sets * bbu_cost
                            io_cost_arr[t] += slice_info[s][-1][t] * slice_info[s][-2][2]   # Traffic * L_C
                            cpu2cloud = (slice_info[s][0][0] + slice_info[s][1][0]) * slice_info[s][-1][t]
                            mem2cloud = (slice_info[s][0][1] + slice_info[s][1][1]) * slice_info[s][-1][t]
                            acc2cloud = (slice_info[s][0][2] + slice_info[s][1][2]) * slice_info[s][-1][t]
                            cloud_cost_arr[t] += (cpu2cloud + acc2cloud * cpu_acc_ratio) * cloud_cpu_cost + mem2cloud * cloud_mem_cost

                            if prev_state[s] == 0:
                                time_state[s] = [frozen_period, frozen_period, max(0, time_state[s][2]-1)]
                            elif prev_state[s] == 1:
                                time_state[s] = [max(0, time_state[s][0]-1),frozen_period, max(0, time_state[s][2]-1)]
                            elif prev_state[s] == 2:
                                time_state[s] = [max(0, time_state[s][0]-1), max(0, time_state[s][1]-1), max(0, time_state[s][2]-1)]
                            elif prev_state[s] == 3:
                                time_state[s] = [max(0, time_state[s][0]-1), max(0, time_state[s][1]-1), frozen_period]
                        else:
                            cpu2bbu -= slice_info[s][2][0] * slice_info[s][-1][t]
                            men2bbu -= slice_info[s][2][1] * slice_info[s][-1][t]          
                            acc2bbu -= slice_info[s][2][2] * slice_info[s][-1][t]          

                if not feasible:   # 尝试CCC
                    time_state_changeble = False
                    if prev_state[s] == 0:
                        time_state_changeble = ((time_state[s][0] == 0) and (time_state[s][1] == 0) and (time_state[s][2] == 0))
                    elif prev_state[s] == 1:
                        time_state_changeble = ((time_state[s][1] == 0) and (time_state[s][2] == 0))
                    elif prev_state[s] == 2:
                        time_state_changeble = (time_state[s][2] == 0)
                    elif prev_state[s] == 3:
                        time_state_changeble = True

                    if time_state_changeble == True:
                        strategy[s][t] = 3 # CCC
                        prev_state[s] = 3
                        io_cost_arr[t] += slice_info[s][-1][t] * slice_info[s][-2][3]  # Traffic * L_D
                        cloud_cost_arr[t] += (required_cpu_basic + required_acc_basic * cpu_acc_ratio) * cloud_cpu_cost + required_mem_basic * cloud_mem_cost

                        if prev_state[s] == 0:
                            time_state[s] = [frozen_period, frozen_period, frozen_period]
                        elif prev_state[s] == 1:
                            time_state[s] = [max(0, time_state[s][0]-1),frozen_period, frozen_period]
                        elif prev_state[s] == 2:
                            time_state[s] = [max(0, time_state[s][0]-1), max(0, time_state[s][1]-1), frozen_period]
                        elif prev_state[s] == 3:
                            time_state[s] = [max(0, time_state[s][0]-1), max(0, time_state[s][1]-1), max(0, time_state[s][2]-1)]

        bbu_sets = compute_bbu_sets(cpu2bbu, men2bbu, acc2bbu)
        if bbu_sets > bbu_b:
            print("Invalid solution")
            break

        if io_cost_arr[t] >= min_bandwidth:
            io_cost_arr[t] += (io_cost_arr[t] - min_bandwidth) * penalty
            
        # if t != 0:
        #     cnt = 0
        #     for s in range(slices_num):
        #         cnt += abs(strategy[s][t]-strategy[s][t-1])
        #     switch_action_cost_arr[t] = cnt * action_cost 

    end = time.time()

    # write file
    file_id = file.split('.')[0].split('e')[-1]
    output_file = "myOutput/"+file_id+".csv"
    with open(output_file, 'w') as f:
        print("file id", file_id)

         
        for s in range(slices_num):     
            line = []
            for t in range(time_horizon):
                if strategy[s][t] == 0:
                    line.append("BBB")
                elif strategy[s][t] == 1:
                    line.append("CBB")
                elif strategy[s][t] == 2:
                    line.append("CCB")
                else:
                    line.append("CCC")
            f.writelines(" ".join(line))
            f.writelines("\n")

        opex = 0
        for t in range(time_horizon):
            opex += cloud_cost_arr[t]
            opex += bbu_cost_arr[t]
            opex += io_cost_arr[t]
            # opex += switch_action_cost_arr[t]
        print("opex:", opex)

        score = max(0, baseline_cost / opex - 1)
        print("score:", score)
        
        res += score
        # res.append(score)

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



print("sum score is", res)