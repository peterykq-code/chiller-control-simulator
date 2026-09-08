function modelPath = build_stage3b_model()
%BUILD_STAGE3B_MODEL Create the Stage 3B two-node Simulink model.

projectRoot = fileparts(fileparts(mfilename("fullpath")));
modelDirectory = fullfile(projectRoot, "matlab");
modelName = "stage3b_chilled_water";
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

add_block("simulink/Discrete/Unit Delay", modelName + "/CHWS State", ...
    "InitialCondition", "8.0", "SampleTime", "10", ...
    "Position", [110 180 180 220]);
add_block("simulink/Discrete/Unit Delay", modelName + "/CHWR State", ...
    "InitialCondition", "9.435406698564593", "SampleTime", "10", ...
    "Position", [110 485 180 525]);

add_block("simulink/Sources/Constant", modelName + "/CHWS Setpoint", ...
    "Value", "7.0", "Position", [110 50 180 80]);
add_block("simulink/Math Operations/Sum", modelName + "/Temperature Error", ...
    "Inputs", "+-", "Position", [260 95 285 135]);
add_block("simulink/Math Operations/Gain", modelName + "/Kp", ...
    "Gain", "0.3", "Position", [335 95 405 135]);
add_block("simulink/Discontinuities/Saturation", modelName + "/Cooling Limit", ...
    "LowerLimit", "0", "UpperLimit", "1", ...
    "Position", [455 90 525 140]);
add_block("simulink/Math Operations/Gain", modelName + "/Maximum Cooling", ...
    "Gain", "100", "Position", [580 95 655 135]);

add_block("simulink/Math Operations/Sum", modelName + "/Return minus Supply", ...
    "Inputs", "+-", "Position", [285 330 310 380]);
add_block("simulink/Math Operations/Gain", modelName + "/Flow Heat Transfer", ...
    "Gain", "5.0*4.18", "Position", [365 330 455 380]);

add_block("simulink/Sources/Step", modelName + "/Building Load", ...
    "Time", "600", "Before", "30", "After", "50", "SampleTime", "10", ...
    "Position", [120 620 190 660]);
add_block("simulink/Math Operations/Sum", modelName + "/Supply Net Heat", ...
    "Inputs", "+-", "Position", [730 250 755 300]);
add_block("simulink/Math Operations/Gain", modelName + "/Supply Temperature Change", ...
    "Gain", "10/(500*4.18)", "Position", [815 250 920 300]);
add_block("simulink/Math Operations/Sum", modelName + "/Next CHWS", ...
    "Inputs", "++", "Position", [995 180 1020 230]);

add_block("simulink/Math Operations/Sum", modelName + "/Return Net Heat", ...
    "Inputs", "+-", "Position", [580 535 605 585]);
add_block("simulink/Math Operations/Gain", modelName + "/Return Temperature Change", ...
    "Gain", "10/(500*4.18)", "Position", [665 535 770 585]);
add_block("simulink/Math Operations/Sum", modelName + "/Next CHWR", ...
    "Inputs", "++", "Position", [845 485 870 535]);

add_block("simulink/Sinks/To Workspace", modelName + "/Log CHWS", ...
    "VariableName", "sim_supply", "SaveFormat", "Timeseries", ...
    "Position", [1100 180 1195 210]);
add_block("simulink/Sinks/To Workspace", modelName + "/Log CHWR", ...
    "VariableName", "sim_return", "SaveFormat", "Timeseries", ...
    "Position", [950 485 1045 515]);
add_block("simulink/Sinks/To Workspace", modelName + "/Log Load", ...
    "VariableName", "sim_load", "SaveFormat", "Timeseries", ...
    "Position", [260 620 355 650]);
add_block("simulink/Sinks/To Workspace", modelName + "/Log Cooling", ...
    "VariableName", "sim_cooling", "SaveFormat", "Timeseries", ...
    "Position", [730 80 825 110]);
add_block("simulink/Sinks/To Workspace", modelName + "/Log Flow Heat", ...
    "VariableName", "sim_flow_heat", "SaveFormat", "Timeseries", ...
    "Position", [500 395 595 425]);

add_line(modelName, "CHWS State/1", "Temperature Error/1", "autorouting", "on");
add_line(modelName, "CHWS Setpoint/1", "Temperature Error/2", "autorouting", "on");
add_line(modelName, "Temperature Error/1", "Kp/1");
add_line(modelName, "Kp/1", "Cooling Limit/1");
add_line(modelName, "Cooling Limit/1", "Maximum Cooling/1");
add_line(modelName, "Maximum Cooling/1", "Supply Net Heat/2", "autorouting", "on");
add_line(modelName, "Maximum Cooling/1", "Log Cooling/1", "autorouting", "on");

add_line(modelName, "CHWR State/1", "Return minus Supply/1", "autorouting", "on");
add_line(modelName, "CHWS State/1", "Return minus Supply/2", "autorouting", "on");
add_line(modelName, "Return minus Supply/1", "Flow Heat Transfer/1");
add_line(modelName, "Flow Heat Transfer/1", "Supply Net Heat/1", "autorouting", "on");
add_line(modelName, "Flow Heat Transfer/1", "Return Net Heat/2", "autorouting", "on");
add_line(modelName, "Flow Heat Transfer/1", "Log Flow Heat/1", "autorouting", "on");

add_line(modelName, "Building Load/1", "Return Net Heat/1", "autorouting", "on");
add_line(modelName, "Building Load/1", "Log Load/1", "autorouting", "on");
add_line(modelName, "Supply Net Heat/1", "Supply Temperature Change/1");
add_line(modelName, "Supply Temperature Change/1", "Next CHWS/2", "autorouting", "on");
add_line(modelName, "CHWS State/1", "Next CHWS/1", "autorouting", "on");
add_line(modelName, "Next CHWS/1", "CHWS State/1", "autorouting", "on");

add_line(modelName, "Return Net Heat/1", "Return Temperature Change/1");
add_line(modelName, "Return Temperature Change/1", "Next CHWR/2", "autorouting", "on");
add_line(modelName, "CHWR State/1", "Next CHWR/1", "autorouting", "on");
add_line(modelName, "Next CHWR/1", "CHWR State/1", "autorouting", "on");

add_line(modelName, "CHWS State/1", "Log CHWS/1", "autorouting", "on");
add_line(modelName, "CHWR State/1", "Log CHWR/1", "autorouting", "on");

annotationText = sprintf( ...
    "Stage 3B: Python-Simulink cross-validation\nBlue path: CHWS control and energy balance | Orange path: CHWR energy balance");
annotation = Simulink.Annotation(modelName, annotationText);
annotation.Position = [350 15 900 60];
annotation.FontSize = 12;

set_param(modelName + "/CHWS State", "BackgroundColor", "lightBlue");
set_param(modelName + "/CHWR State", "BackgroundColor", "orange");
set_param(modelName + "/Building Load", "BackgroundColor", "yellow");

save_system(modelName, modelPath);
close_system(modelName, 0);
fprintf("Created Simulink model: %s\n", modelPath);
end
