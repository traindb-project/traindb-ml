ProcessBuilder processBuilder = new ProcessBuilder("python", "skeleton.py", "--op_type show_model", "hyperparams.json",.....);

processBuilder.redirectErrorStream(true);
File log = folder.newFile("java-version.log");
processBuilder.redirectOutput(log);

Process process = processBuilder.start();
