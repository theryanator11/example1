import java.awt.Color;
import java.awt.Graphics2D;

public class Player {
    GamePanel gp;
    KeyHandler keyH;
    public int x, y;
    public int speed;
    public int shootCooldown = 0;
    public int buyCooldown = 0;
    
    // NEW: Player Health System
    public int health = 3;
    public int maxHealth = 5;

    public Player(GamePanel gp, KeyHandler keyH) {
        this.gp = gp;
        this.keyH = keyH;
        x = gp.screenWidth / 2 - (gp.tileSize / 2);
        y = gp.screenHeight - (gp.tileSize * 2);
        speed = 5;
    }

    public void update() {
        // Only allow movement and shooting if we are in the normal PLAY state
        if (gp.gameState == gp.STATE_PLAY) {
            if (keyH.upPressed) y -= speed;
            if (keyH.downPressed) y += speed;
            if (keyH.leftPressed) x -= speed;
            if (keyH.rightPressed) x += speed;

            if (x < 0) x = 0;
            if (x > gp.screenWidth - gp.tileSize) x = gp.screenWidth - gp.tileSize;
            if (y < 0) y = 0;
            if (y > gp.screenHeight - gp.tileSize) y = gp.screenHeight - gp.tileSize;

            if (shootCooldown > 0) shootCooldown--;
            if (keyH.spacePressed && shootCooldown == 0) {
                gp.projectiles.add(new Projectile(x + gp.tileSize / 2 - 2, y));
                shootCooldown = 15;
            }

            if (buyCooldown > 0) buyCooldown--;
            if (keyH.tPressed && buyCooldown == 0 && gp.score >= 50) {
                gp.score -= 50;
                gp.turrets.add(new Turret(gp, x, y));
                buyCooldown = 30; 
            }
        }
    }

    public void draw(Graphics2D g2) {
        // Draw Ship
        g2.setColor(Color.BLUE);
        g2.fillRect(x, y, gp.tileSize, gp.tileSize);
        
        // Draw Health Bar
        g2.setColor(Color.RED);
        g2.fillRect(x, y + gp.tileSize + 5, gp.tileSize, 5); // Background
        g2.setColor(Color.GREEN);
        int hpWidth = (int)(((double)health / maxHealth) * gp.tileSize);
        g2.fillRect(x, y + gp.tileSize + 5, hpWidth, 5); // Current HP
    }
}