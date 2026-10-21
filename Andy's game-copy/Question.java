public class Question {
    public String prompt;
    public String answer;

    public Question(String prompt, String answer) {
        this.prompt = prompt;
        // Store answer in lowercase so we can easily compare it later
        this.answer = answer.toLowerCase(); 
    }
}