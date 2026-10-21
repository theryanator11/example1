import java.awt.Color;
import java.awt.Graphics2D;

public class Turret {
    GamePanel gp;
    public int x, y;
    int shootCooldown = 0;

    public Turret(GamePanel gp, int x, int y) {
        this.gp = gp;
        this.x = x;
        this.y = y;
    }

    public void update() {
        if (shootCooldown > 0) shootCooldown--;
        
        if (shootCooldown == 0) {
            int projectileX = x + (gp.tileSize / 2) - 2; 
            gp.projectiles.add(new Projectile(projectileX, y));
            shootCooldown = 60; 
        }
    }

    public void draw(Graphics2D g2) {
        g2.setColor(Color.GREEN);
        g2.fillRect(x, y, gp.tileSize, gp.tileSize);
        g2.setColor(Color.DARK_GRAY);
        g2.fillRect(x + (gp.tileSize / 2) - 4, y - 10, 8, 20); 
    }
}