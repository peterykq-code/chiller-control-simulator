function modelPath = build_stage4b_model()
%BUILD_STAGE4B_MODEL Create the Stage 4B PI-control Simulink model.

projectRoot = fileparts(fileparts(mfilename("fullpath")));
modelDirectory = fullfile(projectRoot, "matlab");
modelName = "stage4b_pi_control";
modelPath = fullfile(modelDirectory, modelName + ".slx");

if bdIsLoaded(modelName)
    close_system(modelName, 0);
end
if isfile(modelPath)
    delete(modelPath);
end

new_system(modelName);
set_param(modelName, ...
    "Solver", "FixedStepDiscrete", ...
    "FixedStep", "10", ...
    "StopTime", "1800", ...
    "ReturnWorkspaceOutputs", "on");

% PI controller: error, proportional path, integral state, and output limit.
add_block("simulink/Sources/Constant", modelName + "/CHWS Setpoint", ...
    "Value", "7.0", "Position", [100 55 170 85]);
add_block("simulink/Math Operations/Sum", modelName + "/Temperature Error", ...
    "Inputs", "+-", "Position", [245 105 270 150]);
add_block("simulink/Math Operations/Gain", modelName + "/Kp", ...
    "Gain", "0.3", "Position", [330 105 400 145]);
add_block("simulink/Discrete/Unit Delay", modelName + "/Integral State", ...
    "InitialCondition", "300", "SampleTime", "10", ...
    "Position", [325 230 395 270]);
add_block("simulink/Math Operations/Gain", modelName + "/Ki", ...
    "Gain", "0.001", "Position", [465 230 535 270]);
add_block("simulink/Math Operations/Gain", modelName + "/Error x dt", ...
    "Gain", "10", "Position", [325 320 395 360]);
add_block("simulink/Math Operations/Sum", modelName + "/Next Integral", ...
    "Inputs", "++", "Position", [470 310 495 365]);
add_block("simulink/Math Operations/Sum", modelName + "/PI Sum", ...
    "Inputs", "++", "Position", [590 135 615 190]);
add_block("simulink/Discontinuities/Saturation", modelName + "/Cooling Limit", ...
    "LowerLimit", "0", "UpperLimit", "1", ...
    "Position", [680 130 750 195]);
add_block("simulink/Math Operations/Gain", modelName + "/Maximum Cooling", ...
    "Gain", "100", "Position", [815 140 895 185]);

% Two-node chilled-water plant retained from Stage 3.
add_block("simulink/Discrete/Unit Delay", modelName + "/CHWS State", ...
    "InitialCondition", "7.0", "SampleTime", "10", ...
    "Position", [100 185 170 225]);
add_block("simulink/Discrete/Unit Delay", modelName + "/CHWR State", ...
    "InitialCondition", "8.435406698564593", "SampleTime", "10", ...
    "Position", [100 565 170 605]);
add_block("simulink/Math Operations/Sum", modelName + "/Return minus Supply", ...
    "Inputs", "+-", "Position", [275 445 300 495]);
add_block("simulink/Math Operations/Gain", modelName + "/Flow Heat Transfer", ...
    "Gain", "5.0*4.18", "Position", [360 445 455 495]);
add_block("simulink/Sources/Step", modelName + "/Building Load", ...
    "Time", "600", "Before", "30", "After", "50", "SampleTime", "10", ...
    "Position", [100 735 175 775]);

add_block("simulink/Math Operations/Sum", modelName + "/Supply Net Heat", ...
    "Inputs", "+-", "Position", [735 365 760 415]);
add_block("simulink/Math Operations/Gain", modelName + "/Supply Temperature Change", ...
    "Gain", "10/(500*4.18)", "Position", [820 365 930 415]);
add_block("simulink/Math Operations/Sum", modelName + "/Next CHWS", ...
    "Inputs", "++", "Position", [1010 270 1035 320]);

add_block("simulink/Math Operations/Sum", modelName + "/Return Net Heat", ...
    "Inputs", "+-", "Position", [560 625 585 675]);
add_block("simulink/Math Operations/Gain", modelName + "/Return Temperature Change", ...
    "Gain", "10/(500*4.18)", "Position", [650 625 760 675]);
add_block("simulink/Math Operations/Sum", modelName + "/Next CHWR", ...
    "Inputs", "++", "Position", [840 565 865 615]);

% Logged signals used for sample-by-sample Python comparison.
add_block("simulink/Sinks/To Workspace", modelName + "/Log CHWS", ...
    "VariableName", "sim_supply", "SaveFormat", "Timeseries", ...
    "Position", [1110 270 1210 300]);
add_block("simulink/Sinks/To Workspace", modelName + "/Log CHWR", ...
    "VariableName", "sim_return", "SaveFormat", "Timeseries", ...
    "Position", [940 565 1040 595]);
add_block("simulink/Sinks/To Workspace", modelName + "/Log Cooling Fraction", ...
    "VariableName", "sim_cooling_fraction", "SaveFormat", "Timeseries", ...
    "Position", [815 70 940 100]);
add_block("simulink/Sinks/To Workspace", modelName + "/Log Integral State", ...
    "VariableName", "sim_integral_state", "SaveFormat", "Timeseries", ...
    "Position", [600 235 720 265]);
add_block("simulink/Sinks/To Workspace", modelName + "/Log Load", ...
    "VariableName", "sim_load", "SaveFormat", "Timeseries", ...
    "Position", [245 735 340 765]);
add_block("simulink/Sinks/To Workspace", modelName + "/Log Flow Heat", ...
    "VariableName", "sim_flow_heat", "SaveFormat", "Timeseries", ...
    "Position", [500 455 600 485]);

% Controller signal path.
add_line(modelName, "CHWS State/1", "Temperature Error/1", "autorouting", "on");
add_line(modelName, "CHWS Setpoint/1", "Temperature Error/2", "autorouting", "on");
add_line(modelName, "Temperature Error/1", "Kp/1");
add_line(modelName, "Temperature Error/1", "Error x dt/1", "autorouting", "on");
add_line(modelName, "Integral State/1", "Ki/1");
add_line(modelName, "Integral State/1", "Next Integral/1", "autorouting", "on");
add_line(modelName, "Integral State/1", "Log Integral State/1", "autorouting", "on");
add_line(modelName, "Error x dt/1", "Next Integral/2");
add_line(modelName, "Next Integral/1", "Integral State/1", "autorouting", "on");
add_line(modelName, "Kp/1", "PI Sum/1", "autorouting", "on");
add_line(modelName, "Ki/1", "PI Sum/2", "autorouting", "on");
add_line(modelName, "PI Sum/1", "Cooling Limit/1");
add_line(modelName, "Cooling Limit/1", "Maximum Cooling/1");
add_line(modelName, "Cooling Limit/1", "Log Cooling Fraction/1", "autorouting", "on");

% Supply and return energy balances.
add_line(modelName, "CHWR State/1", "Return minus Supply/1", "autorouting", "on");
add_line(modelName, "CHWS State/1", "Return minus Supply/2", "autorouting", "on");
add_line(modelName, "Return minus Supply/1", "Flow Heat Transfer/1");
add_line(modelName, "Flow Heat Transfer/1", "Supply Net Heat/1", "autorouting", "on");
add_line(modelName, "Flow Heat Transfer/1", "Return Net Heat/2", "autorouting", "on");
add_line(modelName, "Flow Heat Transfer/1", "Log Flow Heat/1", "autorouting", "on");
add_line(modelName, "Maximum Cooling/1", "Supply Net Heat/2", "autorouting", "on");
add_line(modelName, "Supply Net Heat/1", "Supply Temperature Change/1");
add_line(modelName, "Supply Temperature Change/1", "Next CHWS/2", "autorouting", "on");
add_line(modelName, "CHWS State/1", "Next CHWS/1", "autorouting", "on");
add_line(modelName, "Next CHWS/1", "CHWS State/1", "autorouting", "on");
add_line(modelName, "CHWS State/1", "Log CHWS/1", "autorouting", "on");

add_line(modelName, "Building Load/1", "Return Net Heat/1", "autorouting", "on");
add_line(modelName, "Building Load/1", "Log Load/1", "autorouting", "on");
add_line(modelName, "Return Net Heat/1", "Return Temperature Change/1");
add_line(modelName, "Return Temperature Change/1", "Next CHWR/2", "autorouting", "on");
add_line(modelName, "CHWR State/1", "Next CHWR/1", "autorouting", "on");
add_line(modelName, "Next CHWR/1", "CHWR State/1", "autorouting", "on");
add_line(modelName, "CHWR State/1", "Log CHWR/1", "autorouting", "on");

annotationText = sprintf( ...
    "Stage 4B: Python-Simulink PI cross-validation\nController: Kp 0.3 + Ki 0.001 integral state | Plant: Stage 3 CHWS/CHWR energy balances");
annotation = Simulink.Annotation(modelName, annotationText);
annotation.Position = [360 15 980 60];
annotation.FontSize = 12;

set_param(modelName + "/CHWS State", "BackgroundColor", "lightBlue");
set_param(modelName + "/CHWR State", "BackgroundColor", "orange");
set_param(modelName + "/Integral State", "BackgroundColor", "lightBlue");
set_param(modelName + "/Building Load", "BackgroundColor", "yellow");

save_system(modelName, modelPath);
close_system(modelName, 0);
fprintf("Created Simulink model: %s\n", modelPath);
end
