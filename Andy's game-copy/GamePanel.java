import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Rectangle;
import java.util.ArrayList;
import javax.swing.JPanel;

public class GamePanel extends JPanel implements Runnable {
    
    // SCREEN SETTINGS
    final int originalTileSize = 16; 
    final int scale = 3; 
    public final int tileSize = originalTileSize * scale; 
    final int maxScreenCol = 16;
    final int maxScreenRow = 12;
    public final int screenWidth = tileSize * maxScreenCol;  
    public final int screenHeight = tileSize * maxScreenRow; 
    
    Thread gameThread;
    int FPS = 60;
    
    KeyHandler keyH = new KeyHandler();
    Player player = new Player(this, keyH);
    
    // GAME ENTITIES
    public ArrayList<Projectile> projectiles = new ArrayList<>(); 
    public ArrayList<Enemy> enemies = new ArrayList<>(); 
    public ArrayList<Turret> turrets = new ArrayList<>();
    public ArrayList<EnemyLaser> enemyLasers = new ArrayList<>();
    public ArrayList<Bomb> bombs = new ArrayList<>();
    
    public final int maxEnemies = 8;
    int enemySpawnTimer = 0; 
    public int level = 1;
    public int score = 0;
    public int enemiesDefeated = 0;
    
    String[] correctWords = {"Receive", "Because", "Tomorrow", "Definitely", "Separate", "A lot"};
    String[] incorrectWords = {"Recieve", "Becouse", "Tommorow", "Definitly", "Seperate", "Alot"};

    // GAME STATES & QUIZ SYSTEM
    public final int STATE_PLAY = 0;
    public final int STATE_QUIZ = 1;
    public final int STATE_GAMEOVER = 2;
    public int gameState = STATE_PLAY;
    
    public ArrayList<Question> questionBank = new ArrayList<>();
    public Question currentQuestion = null;
    public String quizFeedback = ""; 
    public int feedbackTimer = 0;

    public GamePanel() {
        this.setPreferredSize(new Dimension(screenWidth, screenHeight));
        this.setBackground(Color.BLACK); 
        this.setDoubleBuffered(true); 
        this.addKeyListener(keyH);
        this.setFocusable(true); 
        
        loadQuestions();
    }
    
    private void loadQuestions() {
        // Questions generated from the uploaded document
        questionBank.add(new Question("What is the past tense of 'write'?", "wrote")); 
        questionBank.add(new Question("What is the past tense of 'catch'?", "caught")); 
        questionBank.add(new Question("What is the past tense of 'forget'?", "forgot")); 
        questionBank.add(new Question("What is the past tense of 'hide'?", "hid")); 
        questionBank.add(new Question("What is the past tense of 'drink'?", "drank")); 
        questionBank.add(new Question("What is the past tense of 'lead'?", "led")); 
        
        questionBank.add(new Question("Sweet food eaten after a meal (desert or dessert)?", "dessert")); 
        questionBank.add(new Question("An area of very dry land (desert or dessert)?", "desert")); 
        questionBank.add(new Question("To reduce value or strength (detract or distract)?", "detract")); 
        questionBank.add(new Question("The middle value in math (median or medium)?", "median")); 
        questionBank.add(new Question("A lesson learned from a story (moral or morale)?", "moral")); 
        questionBank.add(new Question("An enclosing cover for a letter (envelop or envelope)?", "envelope")); 
        questionBank.add(new Question("Occurring very soon (eminent or imminent)?", "imminent")); 
        questionBank.add(new Question("An amount more than usual (access or excess)?", "excess")); 
        questionBank.add(new Question("A large group of people (hoard or horde)?", "horde")); 
        questionBank.add(new Question("To untie or make less tight (loose or lose)?", "loose")); 
    }

    public void startGameThread() {
        gameThread = new Thread(this);
        gameThread.start();
    }

    @Override
    public void run() {
        double drawInterval = 1000000000 / FPS; 
        double delta = 0;
        long lastTime = System.nanoTime();
        long currentTime;

        while (gameThread != null) {
            currentTime = System.nanoTime();
            delta += (currentTime - lastTime) / drawInterval;
            lastTime = currentTime;

            if (delta >= 1) {
                update(); 
                repaint(); 
                delta--;
            }
        }
    }

    public void update() {
        if (gameState == STATE_PLAY) {
            player.update(); 
            
            enemySpawnTimer++;
            int spawnThreshold = Math.max(15, 60 - (level * 4)); 
            
            if (enemySpawnTimer >= spawnThreshold && enemies.size() < maxEnemies) {
                int randomX = (int)(Math.random() * (screenWidth - tileSize));
                
                int enemyType = 1; 
                double rand = Math.random();
                
                if (rand > 0.9) {
                    enemyType = 6; // Blue Inquisitor Ship
                } else if (level == 2) {
                    if (rand > 0.6) enemyType = 2; 
                } else if (level == 3) {
                    if (rand > 0.7) enemyType = 3;      
                    else if (rand > 0.4) enemyType = 2; 
                } else if (level == 4) {
                    if (rand > 0.7) enemyType = 4;      
                    else if (rand > 0.5) enemyType = 3; 
                    else if (rand > 0.3) enemyType = 2; 
                } else if (level >= 5) {
                    if (rand > 0.8) enemyType = 5;      
                    else if (rand > 0.6) enemyType = 4; 
                    else if (rand > 0.4) enemyType = 3; 
                    else if (rand > 0.2) enemyType = 2; 
                }
                
                boolean isCorrect = Math.random() > 0.5; 
                int wordIndex = (int)(Math.random() * correctWords.length);
                String chosenWord = isCorrect ? correctWords[wordIndex] : incorrectWords[wordIndex];
                
                enemies.add(new Enemy(this, randomX, -tileSize, enemyType, chosenWord, isCorrect, level));
                enemySpawnTimer = 0; 
            }

            for (int i = 0; i < turrets.size(); i++) turrets.get(i).update();
            for (int i = 0; i < enemies.size(); i++) {
                Enemy e = enemies.get(i);
                if (e.active) e.update();
                else { enemies.remove(i); i--; }
            }
            for (int i = 0; i < projectiles.size(); i++) {
                Projectile p = projectiles.get(i);
                if (p.active) p.update();
                else { projectiles.remove(i); i--; }
            }
            for (int i = 0; i < enemyLasers.size(); i++) {
                EnemyLaser el = enemyLasers.get(i);
                if (el.active) el.update(this);
                else { enemyLasers.remove(i); i--; }
            }
            for (int i = 0; i < bombs.size(); i++) {
                Bomb b = bombs.get(i);
                if (b.active) b.update(this);
                else { bombs.remove(i); i--; }
            }

            Rectangle playerRect = new Rectangle(player.x, player.y, tileSize, tileSize);
            
            for (EnemyLaser el : enemyLasers) {
                if (el.active && new Rectangle((int)el.x - 4, (int)el.y - 4, 8, 8).intersects(playerRect)) {
                    el.active = false;
                    player.health--;
                }
            }
            
            for (Bomb b : bombs) {
                if (b.active && new Rectangle((int)b.x - 8, (int)b.y - 8, 16, 16).intersects(playerRect)) {
                    player.health--;
                    b.active = false; 
                }
            }
            
            if (player.health <= 0) {
                gameState = STATE_GAMEOVER;
            }

            for (int i = 0; i < projectiles.size(); i++) {
                Projectile p = projectiles.get(i);
                Rectangle pRect = new Rectangle(p.x, p.y, 4, 15); 
                
                for (int j = 0; j < enemies.size(); j++) {
                    Enemy e = enemies.get(j);
                    Rectangle eRect = new Rectangle(e.x, e.y, e.size, e.size);
                    
                    if (p.active && e.active && pRect.intersects(eRect)) {
                        p.active = false; 
                        e.health--;       
                        
                        if (e.health <= 0) {
                            e.active = false; 
                            
                            // TRIGGER QUIZ MENU!
                            if (e.type == 6) {
                                triggerQuiz();
                                break;
                            }
                            
                            if (e.isCorrect == false) {
                                score += (e.type * 10); 
                                enemiesDefeated++;
                            } else {
                                score -= 20; 
                                if (score < 0) score = 0; 
                            }
                            
                            if (e.type == 3) {
                                for(int k = 0; k < 3; k++) {
                                    boolean childIsCorrect = Math.random() > 0.5;
                                    int wIndex = (int)(Math.random() * correctWords.length);
                                    String childWord = childIsCorrect ? correctWords[wIndex] : incorrectWords[wIndex];
                                    enemies.add(new Enemy(this, e.x + (k*20), e.y, 1, childWord, childIsCorrect, level));
                                }
                            }

                            if (enemiesDefeated % 10 == 0 && enemiesDefeated > 0) level++;
                        }
                    }
                }
            }
            
            if (feedbackTimer > 0) feedbackTimer--;
            else quizFeedback = "";
            
        } 
        else if (gameState == STATE_QUIZ) {
            if (keyH.enterPressed) {
                keyH.enterPressed = false; 
                String playerAnswer = keyH.typedText.trim().toLowerCase();
                
                // Safety check so we don't crash if currentQuestion is missing
                if (currentQuestion != null && playerAnswer.equals(currentQuestion.answer)) {
                    quizFeedback = "CORRECT! Health and Points Restored!";
                    score += 100;
                    if (player.health < player.maxHealth) player.health++;
                } else {
                    quizFeedback = "WRONG! The answer was: " + (currentQuestion != null ? currentQuestion.answer : "unknown");
                    score -= 50;
                    if (score < 0) score = 0;
                    player.health--;
                    if (player.health <= 0) gameState = STATE_GAMEOVER;
                }
                
                feedbackTimer = 180; 
                if (gameState != STATE_GAMEOVER) {
                    gameState = STATE_PLAY; 
                    keyH.clearKeys();
                }
            }
        }
    }
    
    private void triggerQuiz() {
        gameState = STATE_QUIZ;
        keyH.typedText = ""; 
        keyH.clearKeys();
        if (questionBank.size() > 0) {
            int randomIndex = (int)(Math.random() * questionBank.size());
            currentQuestion = questionBank.get(randomIndex);
        }
    }

    public void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D) g;
        
        for (int i = 0; i < turrets.size(); i++) turrets.get(i).draw(g2);
        player.draw(g2); 
        for (int i = 0; i < projectiles.size(); i++) projectiles.get(i).draw(g2);
        for (int i = 0; i < enemies.size(); i++) enemies.get(i).draw(g2);
        for (int i = 0; i < enemyLasers.size(); i++) enemyLasers.get(i).draw(g2);
        for (int i = 0; i < bombs.size(); i++) bombs.get(i).draw(g2);
        
        g2.setColor(Color.WHITE);
        g2.setFont(new Font("Arial", Font.BOLD, 16));
        g2.drawString("Score: " + score, 10, 20);
        g2.drawString("Level: " + level, 10, 40);
        
        if (!quizFeedback.isEmpty() && gameState == STATE_PLAY) {
            g2.setColor(Color.YELLOW);
            g2.setFont(new Font("Arial", Font.BOLD, 20));
            g2.drawString(quizFeedback, screenWidth/2 - g2.getFontMetrics().stringWidth(quizFeedback)/2, 80);
        }
        
        if (gameState == STATE_QUIZ) {
            g2.setColor(new Color(0, 0, 0, 200));
            g2.fillRect(0, 0, screenWidth, screenHeight);
            
            g2.setColor(Color.BLUE.darker());
            g2.fillRoundRect(100, 150, screenWidth - 200, 300, 25, 25);
            g2.setColor(Color.WHITE);
            g2.setStroke(new BasicStroke(4));
            g2.drawRoundRect(100, 150, screenWidth - 200, 300, 25, 25);
            
            g2.setFont(new Font("Arial", Font.BOLD, 24));
            g2.drawString("INCOMING TRANSMISSION!", 150, 200);
            
            // Check to ensure the question safely loads
            if (currentQuestion != null) {
                g2.setFont(new Font("Arial", Font.PLAIN, 18));
                g2.drawString(currentQuestion.prompt, 130, 250);
            }
            
            g2.setColor(Color.BLACK);
            g2.fillRect(150, 300, screenWidth - 300, 40);
            g2.setColor(Color.GREEN);
            g2.drawRect(150, 300, screenWidth - 300, 40);
            
            g2.drawString(keyH.typedText + "_", 160, 325);
            
            g2.setColor(Color.LIGHT_GRAY);
            g2.setFont(new Font("Arial", Font.ITALIC, 14));
            g2.drawString("Type your answer and press ENTER...", 150, 370);
        }
        
        if (gameState == STATE_GAMEOVER) {
            g2.setColor(new Color(150, 0, 0, 200));
            g2.fillRect(0, 0, screenWidth, screenHeight);
            g2.setColor(Color.WHITE);
            g2.setFont(new Font("Arial", Font.BOLD, 50));
            g2.drawString("GAME OVER", screenWidth/2 - 150, screenHeight/2);
            g2.setFont(new Font("Arial", Font.PLAIN, 20));
            g2.drawString("Final Score: " + score, screenWidth/2 - 70, screenHeight/2 + 40);
        }
        
        g2.dispose(); 
    }
}