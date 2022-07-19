# PyTorchJobClient SDK for Model Training (Not started yet)

- Sung-Soo Kim
- Updated: 14 July, 2022.

* Related Article: [KServe setup and testing](https://github.com/traindb-project/traindb-ml/tree/main/kserve)
	* PyTorch 모델 적용

### References

* [PyTorchJobClient](https://github.com/kubeflow/pytorch-operator/blob/master/sdk/python/docs/PyTorchJobClient.md)
* [Sample for Kubeflow PyTorchJob SDK](https://notebook.community/kubeflow/pytorch-operator/sdk/python/examples/kubeflow-pytorchjob-sdk)

---

This page describes the method for PyTorch ML model training using Python SDK (PyTorchJobClient).

PyTorchJob is a Kubernetes custom resource to run PyTorch training jobs on Kubernetes. The Kubeflow implementation of PyTorchJob is in training-operator.

## Summary

I summarize these procedures for training models using PyTorchJobClient SDK as the following.

0. Install Required Dependencies
1. Defining a PyTorchJob
2. Creating a PyTorchJob
3. Checking the PyTorchJob Status
4. [Optional] Deleting the PyTorchJob




# Java에서 Python 사용하는 방법

TrainDB-ML을 사용하는 측은 현재 Java로 구현되어 있다. 따라서, Python으로 구현할 PyTorchJobClient를 호출할 수 있는 방법이 있어야 한다.

여기서는 프로세스를 이용하는 방법을 활용할 예정이다.

## 프로세스를 사용하는 방식

자바에서 파이썬 프로그램을 호출하는 방식인데 java.lang.Runtime이나
java.lang.ProcessBuilder를 사용하면 시스템의 프로그램을 실행하고 그
결과를 받아 올 수 있다. 보다 자세한 설명은
<https://www.baeldung.com/java-lang-processbuilder-api> 을 참고한다.

즉, 자바에서 파이썬 프로그램을 실행하고 파이썬이 표준 출력(sdtout)에 쓴
내용을 문자열로 캡처하여 처리하는 방식으로 개발한다. 예를들어, 이미지를
텍스트로 변환하는 프로그램을 파이썬으로 작성한다.

-   자바에서 그 파이썬 프로그램을 실행한다.
-   파이썬 프로그램은 이미지에서 추출한 문자열을 표준 출력에 쓴다.
-   자바에서 그 출력을 문자열에 저장하여 사용한다.

### ProcessBuilder의 기본 사용방법

ProcessBuilder를 생성할 때 명령어와 인자를 전달한다. 인스턴스의 start()
메소드를 실행하고 start 메소드가 반환하는 Process 인스턴스의 watiFor()
메소드를 사용하여 서브 프로세스가 끝날 때까지 기다린다. waitFor()
메소드는 정수값을 반환하는데 보통 0이면 정상이다.

``` java
String command = "C:\\Anaconda3\\envs\\jep\\python.exe";  // 명령어
String arg1 = "F:\\src\\hyeon\\latteonterrace\\python\\python-exe\\src\\python\\test.py"; // 인자
ProcessBuilder builder = new ProcessBuilder(command, arg1);
Process process = builder.start();
int exitVal = process.waitFor();  // 자식 프로세스가 종료될 때까지 기다림
if(exitVal != 0) {
  // 비정상 종료
}
```

위 코드에서는 python.exe를 명령어로 전달하고 실행할 파이썬 프로그램을
인자로 전달했다. 파이썬이 파이썬 프로그램을 실행할 것이다.

자식 프로세스가 표준출력(System.out)으로 출력하는 것을 가져오려면
process.getInputStream()을 사용한다.

``` java
InputStream input = process.getInputStream(); // 자식 프로세스가 System.out에 출력하는 내용 
```

자식 프로세스에게 입력을 전달하려면 process.getOutputStream()을
사용한다.

``` java
OutputStream output = process.getOutputStream(); //자식 프로세스에 입력값 전달
```

파이썬 파일을 실행하여 파이썬 파일에서 System.out으로 출력하는 내용을
가져와서 출력하는 완전한 코드는 다음과 같다.

``` java
String command = "C:\\Anaconda3\\envs\\jep\\python.exe";  // 명령어
String arg1 = "F:\\src\\hyeon\\latteonterrace\\python\\python-exe\\src\\python\\test.py"; // 인자
ProcessBuilder builder = new ProcessBuilder(command, arg1);
Process process = builder.start();
int exitVal = process.waitFor();  // 자식 프로세스가 종료될 때까지 기다림
BufferedReader br = new BufferedReader(new InputStreamReader(process.getInputStream(), "euc-kr")); // 서브 프로세스가 출력하는 내용을 받기 위해
String line;
while ((line = br.readLine()) != null) {
     System.out.println(">>>  " + line); // 표준출력에 쓴다
}
if(exitVal != 0) {
  // 비정상 종료
  System.out.println("서브 프로세스가 비정상 종료되었다.");
}
```

> InputStreamReader를 사용할 때 encoding 옵션을 주는데, 실행되는
> 프로그램이 표준 출력에 출력하는 encoding에 따라 한글이 깨질 수 있다.
> 적절한 encoding 옵션을 주어야 한다.

파이썬에서 파일 쓰기를 하거나 크롤링을 할 때 한글이 깨지는 문제가 있다.
파이썬이 기본 UTF-8이 아니라서 비 영어권 사용자들은 코딩할 때 별도의
옵션을 제공해야 한다. 인코딩 타입을 지정하면 해결할 수 있다.

``` python
file=open(fileName, 'w', encoding='utf-8')
```

크롤링하다가 다음과 같은 에러를 만날 수도 있다.

``` null
UnicodeEncodeError: 'cp949' codec can't encode character ...
```

코드 상단에 다음과 같이 코드를 추가하면 해결할 수 있다.

``` python
import sys 
import io 
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding="utf-8")
```

### redirectErrorStream(true)

ProcessBuilder를 사용하여 서브 프로그램을 실행할 때 어떤 오류가
발생했는지 알 수 없게 된다. redirectErrorStream(true)를 사용하여 표준
에러 출력을 표준 출력으로 쓸 수 있게 할 수 있다.

``` java
ProcessBuilder builder = new ProcessBuilder(pythonExe, pyFilePath + "/test.py");
builder.redirectErrorStream(true);  // 표준 에러도 표준 출력에 쓴다
process = builder.start();
BufferedReader br = new BufferedReader(new InputStreamReader(process.getInputStream(), "utf-8"));
```

이제 서브 프로세스에서 오류가 발생하는 경우 inputStream()을 통해 읽을 수
있다. waitFor()를 사용하여 inputStream을 통해 읽은 내용일 오류인지
정상적인 출력인지 알 수 있다.

``` java
int exitVal = process.waitFor();
if(exitVal != 0)  {
   System.out.println("비정상 종료");
}
```

### 표준 입력과 출력을 Redirecting하기

표준입력과 출력을 파일에 쓰기 원할 수 있다. redirectOutput 메소드를
사용하여 파일과 같은 다른 소스에 쓸 수 있다. 이 경우에
getOutputStream()은 ProcessBuilder.NullOutputStream을 반환한다.

``` java
ProcessBuilder processBuilder = new ProcessBuilder("java", "-version");

processBuilder.redirectErrorStream(true);
File log = folder.newFile("java-version.log");
processBuilder.redirectOutput(log);

Process process = processBuilder.start();
```

표준 출력과 표준 에러를 각각의 파일로 저장할 수 잇다.

``` java
File outputLog = tempFolder.newFile("standard-output.log");
File errorLog = tempFolder.newFile("error.log");

processBuilder.redirectOutput(Redirect.appendTo(outputLog));
processBuilder.redirectError(Redirect.appendTo(errorLog));
```

### 현재 프로세스의 I/O를 상속하기

redirectOutput() 메서드 등으로 Redirect.INHERIT를 지정하면 부모
프로세스에서 바로 System.out으로 출력한 것처럼 하위 프로세스의 출력이
연결된다. System.out으로 따로 스트림을 복사하지 않아도 콘솔에서 결과가
보인다.

이렇게 Redirect.INHERIT로 지정하면 Process.getInputStream() 메서드의
실행 결과는 java.lang.ProcessBuilder\$NullInputStream 클래스가 되며 실제
출력 내용을 스트림으로 전달하지 않는다. redirectOutput() 메서드로 별다른
값을 지정하지 않았을 때의 기본값은 Redirect.PIPE이며 파이프를 통해 부모
프로세스로 출력 결과를 전달한다. 예제 1에서 한 것처럼 기본값일 때는 직접
Process.getInputStream() 메서드로 얻어온 스트림을 다루어야 한다.
redirectOutput(File) 메서드로 직접 스트림을 출력할 파일을 지정할 수도
있다.

``` java
@Test
public void givenProcessBuilder_whenInheritIO_thenSuccess() throws IOException, InterruptedException {
    ProcessBuilder processBuilder = new ProcessBuilder("/bin/sh", "-c", "echo hello");

    processBuilder.inheritIO();
    Process process = processBuilder.start();

    int exitCode = process.waitFor();
    assertEquals("No errors should be detected", 0, exitCode);
}
```

### 기타 고려할 사항

Process를 사용할 때 몇가지 고려할 사항을 알아보자.

-   하위 프로세스는 Process 클래스의 getInputStream() 메서드와
    getErrorStream() 메서드를 통해 출력 메시지를 부모 프로세스에 보낸다.
    이렇게 받은 스트림을 **프로세스의 실행과 동시에 처리하지 않으면 서브
    프로세스는 멈추거나 교착 상태(deadlock)에 빠질 수 있다.** 플랫폼에
    따라서는 표준 입출력으로 데이터를 보내는 버퍼의 크기가 작을 수도
    있어 동시에 스트림을 읽어 스트림을 제거하지 않으면 버퍼가 넘칠 수
    있기 때문이다.
-   JDK 8 이상을 사용한다. 이전 버전은 메모리 문제가 있다.
-   작은 메모리를 차지하는 외부 프로세스 실행 전용 데몬을 만든다. 별도의
    데몬을 만드는 작업이 번거롭다는 이유로 백엔드용 Tomcat을 하나 더
    실행해서 셸 실행 전용 데몬으로 활용하는 경우도 있다. 그런 상황이라면
    그 Tomcat에서 메모리를 과도하게 쓰지 않도록 관리하고 최대 힙
    사이즈는 프런트 서버 용도의 Tomcat보다 훨씬 적게 잡아야 한다.

   
   
   

   
    	


