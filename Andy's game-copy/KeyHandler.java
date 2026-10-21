import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;

public class KeyHandler implements KeyListener {
    public boolean upPressed, downPressed, leftPressed, rightPressed, spacePressed, tPressed;
    
    public String typedText = "";
    public boolean enterPressed = false;

    // NEW FIX: Clears the sticky keys so your ship doesn't fly away after a quiz!
    public void clearKeys() {
        upPressed = false;
        downPressed = false;
        leftPressed = false;
        rightPressed = false;
        spacePressed = false;
        tPressed = false;
        enterPressed = false;
    }

    @Override
    public void keyTyped(KeyEvent e) {
        char c = e.getKeyChar();
        if (c == '\b') {
            if (typedText.length() > 0) {
                typedText = typedText.substring(0, typedText.length() - 1);
            }
        } 
        else if (Character.isLetterOrDigit(c) || c == ' ' || c == '\'') {
            typedText += c;
        }
    }

    @Override
    public void keyPressed(KeyEvent e) {
        int code = e.getKeyCode();
        if (code == KeyEvent.VK_W || code == KeyEvent.VK_UP) upPressed = true;
        if (code == KeyEvent.VK_S || code == KeyEvent.VK_DOWN) downPressed = true;
        if (code == KeyEvent.VK_A || code == KeyEvent.VK_LEFT) leftPressed = true;
        if (code == KeyEvent.VK_D || code == KeyEvent.VK_RIGHT) rightPressed = true;
        if (code == KeyEvent.VK_SPACE) spacePressed = true;
        if (code == KeyEvent.VK_T) tPressed = true;
        if (code == KeyEvent.VK_ENTER) enterPressed = true; 
    }

    @Override
    public void keyReleased(KeyEvent e) {
        int code = e.getKeyCode();
        if (code == KeyEvent.VK_W || code == KeyEvent.VK_UP) upPressed = false;
        if (code == KeyEvent.VK_S || code == KeyEvent.VK_DOWN) downPressed = false;
        if (code == KeyEvent.VK_A || code == KeyEvent.VK_LEFT) leftPressed = false;
        if (code == KeyEvent.VK_D || code == KeyEvent.VK_RIGHT) rightPressed = false;
        if (code == KeyEvent.VK_SPACE) spacePressed = false;
        if (code == KeyEvent.VK_T) tPressed = false;
        if (code == KeyEvent.VK_ENTER) enterPressed = false; 
    }
}