import customtkinter as ctk
from tkinter import filedialog
import pyvisa as visa
import numpy as np
import pandas as pd
import os
import time
import matplotlib.pyplot as plt
from IPython.display import clear_output
from IPython.display import display
from sklearn.linear_model import LinearRegression



class MOKEGUI:

    def __init__(self):
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        

        self.app = ctk.CTk()
        self.app.geometry("750x475")
        self.app.title("MOKE")

        frame = ctk.CTkFrame(master=self.app)
        frame.grid(row=0, column=0, sticky="nsew")

        self.start_button = ctk.CTkButton(master=self.app, text="Start", command=self.toggle)
        self.start_button.place(relx=0.75, rely=0.85, anchor=ctk.CENTER, relwidth=0.2, relheight=0.1)

        self.directory_button = ctk.CTkButton(master=self.app, text="Save Directory", command=self.save_directory)
        self.directory_button.place(relx=0.50, rely=0.85, anchor=ctk.CENTER, relwidth=0.2, relheight=0.1)

        self.calibration_button = ctk.CTkButton(master=self.app, text="Calibration File", command=self.calibration_file)
        self.calibration_button.place(relx=0.25, rely=0.85, anchor=ctk.CENTER, relwidth=0.2, relheight=0.1)

        self.sample_name = ctk.CTkTextbox(master=frame, height=20, width=80)
        self.sample_name.grid(row=0, column=1)

        self.maxV = ctk.CTkTextbox(master=frame, height=20, width=80)
        self.maxV.grid(row=1, column=1, padx=10, pady=5)

        self.stepV = ctk.CTkTextbox(master=frame, height=20, width=80)
        self.stepV.grid(row=2, column=1, padx=10, pady=5)

        self.label_sample = ctk.CTkLabel(master=frame, text="Sample Name")
        self.label_sample.grid(row=0, column=0, padx=10, pady=5)

        self.label_max = ctk.CTkLabel(master=frame, text="Max Voltage (V)")
        self.label_max.grid(row=1, column=0, padx=10, pady=5)

        self.label_step = ctk.CTkLabel(master=frame, text="Step Voltage (V)")
        self.label_step.grid(row=2, column=0, padx=10, pady=5)

        self.app.mainloop()
        
        
    def save_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            print(f"Selected Directory: {directory}")
            self.directory_button.configure(text=directory)
            self.directory = directory

    def calibration_file(self):
        calibration = filedialog.askopenfilename()
        if calibration:
            print(f"Selected Calibration File: {calibration}")
            self.calibration_button.configure(text=calibration)
            self.calibation = calibration


    def toggle(self):
        current = self.start_button.cget("text")
        if current == "Start":
            self.start_button.configure(text="Stop")
            rm = visa.ResourceManager()  #calls the differnt addresses for what is attached to the system
            sm = rm.open_resource('GPIB0::24::INSTR')  #adress and connection for the source meter
            # rm.list_resources()
            lia = rm.open_resource('GPIB0::13::INSTR')  #adress abd connection for the lock in amplifier

            dmm_01 = rm.open_resource('GPIB0::22::INSTR')
            smu = rm.open_resource('GPIB0::24::INSTR')  #adress and connection for the source meter


            def init_smu():
                smu.write('*RST')
                smu.write(':SOUR:FUNC CURR')
                smu.write(':SOUR:CURR:MODE FIXED')
                smu.write(':SOUR:CURR:RANG 0.002')
                smu.write(':SOUR:CURR:LEV 0.001')
                smu.write(':SENS:VOLT:PROT 5')
                smu.write(':SENS:FUNC "VOLT"')
                smu.write(':SENS:VOLT:RANG 2')
                smu.write(':FORM:ELEM VOLT')
                smu.write(':OUTP ON')


            init_smu()

            # print(float(dmm_01.query(":MEAS:VOLT?").split(',')[0]))

            #This is where we want to save our data and graphs to. 
            #save_dir = os.path.join('C:/Users/ramosaponte/Box/Arena_Lab_Data/Leo/MOKE') #File path to save FMR data to.20210816A_Fe90Co10
            save_dir = self.directory
            sample_name = self.sample_name.get()

            calibrationfile = self.calibration

            #Generate fit equation for the calibration data
            model = LinearRegression()  #create a model
            calib_data = pd.read_csv(calibrationfile)

            HV = np.array(calib_data['Hall Voltage(V)'])
            Field = np.array(calib_data['Field (T)'])

            X = HV.reshape(-1, 1)

            model.fit(X, Field)
            slope = model.coef_[0]
            intercept = model.intercept_

            print('Calibration Fit, Field (T) = ', slope, '* Hall_voltage +', intercept)

            # results =pd.DataFrame()

            #this is the voltage output given to the BOP to convert into a current to give to the magnet 
            #negative voltage is positive current

            maxvolt = self.maxV.get
            voltstep = self.stepV.get

            loads = np.arange(0.0, maxvolt, voltstep)
            loads2 = np.arange(-1 * maxvolt, maxvolt, voltstep)
            loads3 = np.arange(maxvolt, -1 * maxvolt, -1 * voltstep)

            # print (loads)
            # print(loads2)
            # print(loads3)

            #combines the two data sets to create a full hystersis loop

            loadtotal = np.concatenate([loads3, loads2])


            def file_date():
                import datetime
                date_today_0 = datetime.datetime.today()
                date_today_1 = str(date_today_0).replace("-", "_").replace(" ", "_time_")
                date_today_2 = str(date_today_1).split('.')[0].replace(":", "_")
                return date_today_2


            #start of MOKE data collection
            #########################################################################################################################
            results = pd.DataFrame()  #creates empty data frame to save data to
            temps = pd.DataFrame()
            lia.write('AUXV 1, 10.0')
            time.sleep(5.0)
            lia.write('APHS')
            #time.sleep(3)
            lia.write('AUXV 1, 10.0')  #saturate the magnet
            time.sleep(1)
            for load in loadtotal:
                lia.write('AUXV 1 ,%.2f' % load)
                Hall_voltage = dmm_01.query(":MEAS:VOLT?")
                time.sleep(0.1)

                lia.write('STRT')  #this starts the data collection for the LIA
                FMR_string = lia.query('SNAP? 1,2')  #this collects the data from X and Y from the LIA and returns it as a string
                #X = FMR signal, Y = background
                FMR_data = FMR_string.split(',')  #this splits the string up accordingly to get the values into an array
                Hall_voltage = dmm_01.query(":MEAS:VOLT?")
                Field_value = (slope * float(Hall_voltage.split(',')[0]) + intercept)
                print(Field_value)
                temp = {"Voltage (V)": load,
                        "MOKE Signal": float(FMR_data[0]),
                        'MOKE BCKGD': float(FMR_data[1]),
                        'Hall Voltage(V)': float(Hall_voltage.split(',')[0]),
                        'Field (T)': Field_value}  #Creating a temporary array to store all of our values to before appending to dataframe.
                results = results.append(temp,
                                         #We build the results dataframe row by row by adding the temp array for every for loop/voltage
                                         ignore_index=True)  #Resets indexing so rows appear in the order appended/added.

                #pd_append = {"Voltage": load,
                #            "X": float(mylist[0]),
                #             "Y": float(mylist[1])}
                # temps = temps.append(pd_append, ignore_index=True)

                # temp['X']=float(mylist[0])#this makes the X col of data in the data structure from the array mylist
                #temp['Y']=float(mylist[1])#this makes the Y col of the data in the data strucutre from the array mylist
                #results=results.append(temp,ignore_index=True)

                #Plot current data
                plt.show(
                    block=False)  #If running in terminal, block = False will let the code keep running w/o closing the graph window
                plt.xlabel('Field (T)')
                plt.ylabel('Moke signal')
                plt.title(sample_name)
                plt.plot(results['Field (T)'],
                         results['MOKE Signal'], '-b',
                         label='MOKE Signal')  #Setup what data is to be plotted. If you want lines instead of scatter omit 'o'.
                #plt.plot(results['Voltage (V)'], 
                #            results['FMR BCKGD'], '-r',
                #        label = "FMR Background")
                #plt.title(str(freq) + " GHz") #NEEDS TO BE SAMPLE NAME
                #plt.legend(bbox_to_anchor = (1.05 , 1), loc = 2)
                plt.grid('on')
                plt.tight_layout()
                clear_output(
                    wait=True)  #Clears current graph in order to make way for updated plot, wait = True means it waits to clear until new graph is ready
                display(plt.gcf())
                time.sleep(0.1)

            clear_output(wait=True)
            plt.savefig(save_dir + sample_name + "_noPI" + str(
                file_date()) + '.png')  #Export FMR graph    ##NEED TO ADD SAMPLE TITLE AS USER INPUT
            lia.write('AUXV 1, 0')  #sets field to zero
            results.to_csv(save_dir + sample_name + "_noPI" + str(file_date()) + '.csv',
                           index=False)  #Saves FMR data to current directory
            #index = False skips saving the index values to the CSV.
        else:
            self.start_button.configure(text="Start")

    



MOKEGUI()













# -*- coding: utf-8 -*-
"""
Created on Tue Jul 18 12:02:34 2023

@author: ayomipo
"""

'''
<-----------------------------QUICK INSTRUCTIONS------------------------------------>

-Make sure you use the most recent calibration file. You can change the calibration file path
-Turn on multimeter to record Hall voltage
-Turn on current source. The desired amperage is automatically set to 1mA

'''


# from mcculw import ul

rm = visa.ResourceManager()  #calls the differnt addresses for what is attached to the system
sm = rm.open_resource('GPIB0::24::INSTR')  #adress and connection for the source meter
# rm.list_resources()
lia = rm.open_resource('GPIB0::13::INSTR')  #adress abd connection for the lock in amplifier

dmm_01 = rm.open_resource('GPIB0::22::INSTR')
smu = rm.open_resource('GPIB0::24::INSTR')  #adress and connection for the source meter


def init_smu():
    smu.write('*RST')
    smu.write(':SOUR:FUNC CURR')
    smu.write(':SOUR:CURR:MODE FIXED')
    smu.write(':SOUR:CURR:RANG 0.002')
    smu.write(':SOUR:CURR:LEV 0.001')
    smu.write(':SENS:VOLT:PROT 5')
    smu.write(':SENS:FUNC "VOLT"')
    smu.write(':SENS:VOLT:RANG 2')
    smu.write(':FORM:ELEM VOLT')
    smu.write(':OUTP ON')


init_smu()

# print(float(dmm_01.query(":MEAS:VOLT?").split(',')[0]))

#This is where we want to save our data and graphs to. 
#save_dir = os.path.join('C:/Users/ramosaponte/Box/Arena_Lab_Data/Leo/MOKE') #File path to save FMR data to.20210816A_Fe90Co10
save_dir = moke_instance.directory
sample_name = moke_instance.name_sample

calibrationfile = moke_instance.calibration

#Generate fit equation for the calibration data
model = LinearRegression()  #create a model
calib_data = pd.read_csv(calibrationfile)

HV = np.array(calib_data['Hall Voltage(V)'])
Field = np.array(calib_data['Field (T)'])

X = HV.reshape(-1, 1)

model.fit(X, Field)
slope = model.coef_[0]
intercept = model.intercept_

print('Calibration Fit, Field (T) = ', slope, '* Hall_voltage +', intercept)

# results =pd.DataFrame()

#this is the voltage output given to the BOP to convert into a current to give to the magnet 
#negative voltage is positive current

maxvolt = moke_instance.max_volt
voltstep = moke_instance.step_volt

loads = np.arange(0.0, maxvolt, voltstep)
loads2 = np.arange(-1 * maxvolt, maxvolt, voltstep)
loads3 = np.arange(maxvolt, -1 * maxvolt, -1 * voltstep)

# print (loads)
# print(loads2)
# print(loads3)

#combines the two data sets to create a full hystersis loop

loadtotal = np.concatenate([loads3, loads2])


def file_date():
    import datetime
    date_today_0 = datetime.datetime.today()
    date_today_1 = str(date_today_0).replace("-", "_").replace(" ", "_time_")
    date_today_2 = str(date_today_1).split('.')[0].replace(":", "_")
    return date_today_2


#start of MOKE data collection
#########################################################################################################################
results = pd.DataFrame()  #creates empty data frame to save data to
temps = pd.DataFrame()
lia.write('AUXV 1, 10.0')
time.sleep(5.0)
lia.write('APHS')
#time.sleep(3)
lia.write('AUXV 1, 10.0')  #saturate the magnet
time.sleep(1)
for load in loadtotal:
    lia.write('AUXV 1 ,%.2f' % load)
    Hall_voltage = dmm_01.query(":MEAS:VOLT?")
    time.sleep(0.1)

    lia.write('STRT')  #this starts the data collection for the LIA
    FMR_string = lia.query('SNAP? 1,2')  #this collects the data from X and Y from the LIA and returns it as a string
    #X = FMR signal, Y = background
    FMR_data = FMR_string.split(',')  #this splits the string up accordingly to get the values into an array
    Hall_voltage = dmm_01.query(":MEAS:VOLT?")
    Field_value = (slope * float(Hall_voltage.split(',')[0]) + intercept)
    print(Field_value)
    temp = {"Voltage (V)": load,
            "MOKE Signal": float(FMR_data[0]),
            'MOKE BCKGD': float(FMR_data[1]),
            'Hall Voltage(V)': float(Hall_voltage.split(',')[0]),
            'Field (T)': Field_value}  #Creating a temporary array to store all of our values to before appending to dataframe.
    results = results.append(temp,
                             #We build the results dataframe row by row by adding the temp array for every for loop/voltage
                             ignore_index=True)  #Resets indexing so rows appear in the order appended/added.

    #pd_append = {"Voltage": load,
    #            "X": float(mylist[0]),
    #             "Y": float(mylist[1])}
    # temps = temps.append(pd_append, ignore_index=True)

    # temp['X']=float(mylist[0])#this makes the X col of data in the data structure from the array mylist
    #temp['Y']=float(mylist[1])#this makes the Y col of the data in the data strucutre from the array mylist
    #results=results.append(temp,ignore_index=True)

    #Plot current data
    plt.show(
        block=False)  #If running in terminal, block = False will let the code keep running w/o closing the graph window
    plt.xlabel('Field (T)')
    plt.ylabel('Moke signal')
    plt.title(sample_name)
    plt.plot(results['Field (T)'],
             results['MOKE Signal'], '-b',
             label='MOKE Signal')  #Setup what data is to be plotted. If you want lines instead of scatter omit 'o'.
    #plt.plot(results['Voltage (V)'], 
    #            results['FMR BCKGD'], '-r',
    #        label = "FMR Background")
    #plt.title(str(freq) + " GHz") #NEEDS TO BE SAMPLE NAME
    #plt.legend(bbox_to_anchor = (1.05 , 1), loc = 2)
    plt.grid('on')
    plt.tight_layout()
    clear_output(
        wait=True)  #Clears current graph in order to make way for updated plot, wait = True means it waits to clear until new graph is ready
    display(plt.gcf())
    time.sleep(0.1)

clear_output(wait=True)
plt.savefig(save_dir + sample_name + "_noPI" + str(
    file_date()) + '.png')  #Export FMR graph    ##NEED TO ADD SAMPLE TITLE AS USER INPUT
lia.write('AUXV 1, 0')  #sets field to zero
results.to_csv(save_dir + sample_name + "_noPI" + str(file_date()) + '.csv',
               index=False)  #Saves FMR data to current directory
#index = False skips saving the index values to the CSV.

#Six repetitions
#start of MOKE data collection
#########################################################################################################################
for n in np.arange(0.0, 6.0):
    results = pd.DataFrame()  #creates empty data frame to save data to
    temps = pd.DataFrame()
    lia.write('AUXV 1, 9.0')
    time.sleep(5.0)
    lia.write('APHS')
    #time.sleep(3)
    lia.write('AUXV 1, 9.0')  #saturate the magnet
    time.sleep(1)
    for load in loadtotal:
        lia.write('AUXV 1 ,%.2f' % load)
        Hall_voltage = dmm_01.query(":MEAS:VOLT?")
        time.sleep(0.1)

        lia.write('STRT')  #this starts the data collection for the LIA
        FMR_string = lia.query(
            'SNAP? 1,2')  #this collects the data from X and Y from the LIA and returns it as a string
        #X = FMR signal, Y = background
        FMR_data = FMR_string.split(',')  #this splits the string up accordingly to get the values into an array
        Hall_voltage = dmm_01.query(":MEAS:VOLT?")
        Field_value = (slope * float(Hall_voltage.split(',')[0]) + intercept)

        temp = {"Voltage (V)": load,
                "MOKE Signal": float(FMR_data[0]),
                'MOKE BCKGD': float(FMR_data[1]),
                'Hall Voltage(V)': float(Hall_voltage.split(',')[0]),
                'Field (T)': Field_value}  #Creating a temporary array to store all of our values to before appending to dataframe.
        results = results.append(temp,
                                 #We build the results dataframe row by row by adding the temp array for every for loop/voltage
                                 ignore_index=True)  #Resets indexing so rows appear in the order appended/added.

        #pd_append = {"Voltage": load,
        #            "X": float(mylist[0]),
        #             "Y": float(mylist[1])}
        # temps = temps.append(pd_append, ignore_index=True)

        # temp['X']=float(mylist[0])#this makes the X col of data in the data structure from the array mylist
        #temp['Y']=float(mylist[1])#this makes the Y col of the data in the data strucutre from the array mylist
        #results=results.append(temp,ignore_index=True)

        #Plot current data
        plt.show(
            block=False)  #If running in terminal, block = False will let the code keep running w/o closing the graph window
        plt.xlabel('Field (T)')
        plt.ylabel('Moke signal')
        plt.plot(results['Field (T)'],
                 results['MOKE Signal'], '-b',
                 label='MOKE Signal')  #Setup what data is to be plotted. If you want lines instead of scatter omit 'o'.
        #plt.plot(results['Voltage (V)'],
        #            results['FMR BCKGD'], '-r',
        #        label = "FMR Background")
        #plt.title(str(freq) + " GHz") #NEEDS TO BE SAMPLE NAME
        #plt.legend(bbox_to_anchor = (1.05 , 1), loc = 2)
        plt.grid('on')
        plt.tight_layout()
        clear_output(
            wait=True)  #Clears current graph in order to make way for updated plot, wait = True means it waits to clear until new graph is ready
        display(plt.gcf())
        time.sleep(1.0)

    clear_output(wait=True)
    plt.savefig(save_dir + sample_name + str(
        file_date()) + '.png')  #Export FMR graph    ##NEED TO ADD SAMPLE TITLE AS USER INPUT
    lia.write('AUXV 1, 0')  #sets field to zero
    results.to_csv(save_dir + sample_name + str(file_date()) + '.csv',
                   index=False)  #Saves FMR data to current directory
    #index = False skips saving the index values to the CSV.
