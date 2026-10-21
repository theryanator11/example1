import java.awt.Color;
import java.awt.Graphics2D;

public class Bomb {
    public double x, y;
    public boolean active = true;
    
    private int detonateY; 
    private int type;
    private Color bombColor;

    public Bomb(int startX, int startY, GamePanel gp, int currentLevel) {
        this.x = startX;
        this.y = startY;
        this.detonateY = gp.screenHeight / 3 + (int)(Math.random() * (gp.screenHeight / 3));
        
        if (currentLevel < 3) this.type = 1; 
        else if (currentLevel < 5) this.type = (int)(Math.random() * 2) + 1; 
        else this.type = (int)(Math.random() * 4) + 1; 

        if (type == 1) bombColor = Color.YELLOW;       
        else if (type == 2) bombColor = Color.CYAN;    
        else if (type == 3) bombColor = Color.MAGENTA; 
        else if (type == 4) bombColor = Color.ORANGE;  
    }

    public void update(GamePanel gp) {
        y += 2.5; 
        
        if (y >= detonateY) {
            active = false; 
            double speed = 2.5; 
            
            if (type == 1) { 
                for (int i = 0; i < 8; i++) {
                    double angle = Math.toRadians(i * 45); 
                    gp.enemyLasers.add(new EnemyLaser(x, y, Math.cos(angle) * speed, Math.sin(angle) * speed));
                }
            } 
            else if (type == 2) { 
                gp.enemyLasers.add(new EnemyLaser(x, y, speed, 0));
                gp.enemyLasers.add(new EnemyLaser(x, y, -speed, 0));
                gp.enemyLasers.add(new EnemyLaser(x, y, 0, speed));
                gp.enemyLasers.add(new EnemyLaser(x, y, 0, -speed));
            }
            else if (type == 3) { 
                double diag = speed * 0.8;
                gp.enemyLasers.add(new EnemyLaser(x, y, diag, diag));
                gp.enemyLasers.add(new EnemyLaser(x, y, -diag, diag));
                gp.enemyLasers.add(new EnemyLaser(x, y, diag, -diag));
                gp.enemyLasers.add(new EnemyLaser(x, y, -diag, -diag));
            }
            else if (type == 4) { 
                gp.enemyLasers.add(new EnemyLaser(x, y, 0, speed + 1));        
                gp.enemyLasers.add(new EnemyLaser(x, y, speed * 0.6, speed));  
                gp.enemyLasers.add(new EnemyLaser(x, y, -speed * 0.6, speed)); 
            }
        }
    }

    public void draw(Graphics2D g2) {
        g2.setColor(bombColor);
        g2.fillOval((int)x - 8, (int)y - 8, 16, 16);
        g2.setColor(Color.WHITE);
        g2.fillOval((int)x - 4, (int)y - 4, 8, 8);
    }
}