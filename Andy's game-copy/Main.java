import javax.swing.JFrame;

public class Main {
    public static void main(String[] args) {
        // Create the window
        JFrame window = new JFrame("Grammar Defender: Space Rescue");
        window.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        window.setResizable(false); // Prevents the player from resizing the screen
        
        // Create and add the game panel
        GamePanel gamePanel = new GamePanel();
        window.add(gamePanel);
        
        // Pack fits the window perfectly around our GamePanel
        window.pack(); 
        
        window.setLocationRelativeTo(null); // Centers the window on the screen
        window.setVisible(true);
        
        // Start the game engine
        gamePanel.startGameThread();
    }
}