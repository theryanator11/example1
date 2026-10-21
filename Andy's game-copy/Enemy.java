import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Font;
import java.awt.Graphics2D;

public class Enemy {
    GamePanel gp;
    public double exactX, exactY;
    public int x, y;
    public int health, maxHealth, type, size;
    public Color alienColor; 
    public boolean active = true;
    public String word;
    public boolean isCorrect;

    private double targetX, targetY;
    private double rotationAngle = 0; 
    private int shootCooldown;

    public Enemy(GamePanel gp, int startX, int startY, int type, String word, boolean isCorrect, int currentLevel) {
        this.gp = gp;
        this.type = type;
        this.word = word;
        this.isCorrect = isCorrect;
        
        this.exactX = startX;
        this.exactY = startY;
        this.size = (int)(gp.tileSize * 0.6); 
        this.shootCooldown = 60 + (int)(Math.random() * 120); 

        pickNewTarget(); 

        if (type == 1) {
            alienColor = new Color(200, 50, 50); 
            health = maxHealth = 1 + (currentLevel / 3); 
        } else if (type == 2) {
            alienColor = new Color(230, 130, 10); 
            health = maxHealth = 1 + (currentLevel / 3); 
        } else if (type == 3) {
            alienColor = new Color(150, 0, 150); 
            health = maxHealth = 5 + (currentLevel / 2); 
            this.size = (int)(gp.tileSize * 1.1); 
        } else if (type == 4) {
            alienColor = new Color(0, 200, 200); 
            health = maxHealth = 1 + (currentLevel / 4);
        } else if (type == 5) {
            alienColor = new Color(50, 200, 50); 
            health = maxHealth = 2 + (currentLevel / 3);
        } else if (type == 6) {
            // NEW: The Blue Inquisitor Ship!
            alienColor = new Color(0, 100, 255); 
            // FIXED: The 'speed = 2;' error line has been removed from here!
            health = maxHealth = 1; 
            this.word = "? QUIZ ?"; 
        }
    }

    private void pickNewTarget() {
        targetX = Math.random() * (gp.screenWidth - size);
        targetY = Math.random() * (gp.screenHeight * 0.4);
    }

    public void update() {
        rotationAngle += 0.05; 

        exactX += (targetX - exactX) * 0.02;
        exactY += (targetY - exactY) * 0.02;

        if (Math.abs(targetX - exactX) < 10 && Math.abs(targetY - exactY) < 10) {
            pickNewTarget();
        }

        shootCooldown--;
        if (shootCooldown <= 0) {
            if (type == 3) {
                gp.bombs.add(new Bomb((int)exactX + size/2, (int)exactY + size, gp, gp.level));
                shootCooldown = Math.max(50, 180 - (gp.level * 15)); 
            } else if (type != 6) { 
                // Type 6 ships don't shoot!
                gp.enemyLasers.add(new EnemyLaser((int)exactX + size/2, (int)exactY + size, 0, 4));
                shootCooldown = 60 + (int)(Math.random() * 120);
            }
        }

        x = (int)exactX; 
        y = (int)exactY; 
    }

    public void draw(Graphics2D g2) {
        g2.translate(x + size/2, y + size/2); 
        g2.rotate(Math.sin(rotationAngle) * 0.15); 
        
        int drawX = -size/2;
        int drawY = -size/2;

        Color hullColor = new Color(100, 105, 110); 
        Color darkHull = hullColor.darker();
        Color eyeColor = alienColor.brighter();

        g2.setColor(alienColor);
        g2.fillOval(drawX + (int)(size*0.1), drawY + (int)(size*0.2), (int)(size*0.8), (int)(size*0.7));
        g2.fillOval(drawX - (int)(size*0.1), drawY + (int)(size*0.4), (int)(size*0.5), (int)(size*0.5));
        
        g2.setColor(hullColor);
        g2.fillOval(drawX, drawY + (int)(size*0.3), size, (int)(size*0.4)); 
        g2.setColor(darkHull);
        g2.setStroke(new BasicStroke(2));
        g2.drawOval(drawX, drawY + (int)(size*0.3), size, (int)(size*0.4)); 

        g2.setColor(new Color(100, 200, 255, 150));
        g2.fillOval(drawX + (int)(size*0.25), drawY + (int)(size*0.1), (int)(size*0.5), (int)(size*0.4));
        
        g2.setColor(alienColor.darker());
        g2.setStroke(new BasicStroke(1));
        g2.drawLine(drawX + size/2, drawY + (int)(size*0.15), drawX + (int)(size*0.4), drawY + (int)(size*0.3));

        g2.setColor(eyeColor);
        g2.fillOval(drawX + (int)(size*0.35), drawY + (int)(size*0.45), (int)(size*0.08), (int)(size*0.08));
        g2.fillOval(drawX + (int)(size*0.57), drawY + (int)(size*0.45), (int)(size*0.08), (int)(size*0.08));

        g2.rotate(-Math.sin(rotationAngle) * 0.15);
        g2.translate(-(x + size/2), -(y + size/2));

        g2.setColor(Color.WHITE);
        g2.setFont(new Font("Courier New", Font.BOLD, 14)); 
        int textX = x + (size / 2) - (g2.getFontMetrics().stringWidth(word) / 2);
        g2.drawString(word, textX, y - 5);
    }
}