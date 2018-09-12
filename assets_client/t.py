import platform
import win32com
import wmi


cpu_lists = wmi.WMI().Win32_Processor()
print(cpu_lists[0].Name)
cpu_core_count = 0
for cpu in cpu_lists:
    cpu_core_count += cpu.NumberOfCores
print(cpu_core_count)

