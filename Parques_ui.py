import sys
import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QComboBox, QPushButton
from PyQt5.QtGui import QPixmap
from PyQt5 import uic

class MiVentana(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("Parques.ui", self)
        
        self.btndados.clicked.connect(self.lanzar_dados)
        self.btnsiguiente.clicked.connect(self.cambiar_turno)
        
        # Listas de fichas (QPushButton)
        self.fichas_j1 = [self.f1, self.f2, self.f3, self.f4]
        self.fichas_j2 = [self.j2f1, self.j2f2, self.j2f3, self.j2f4]
        self.fichas_j3 = [self.j3f1, self.j3f2, self.j3f3, self.j3f4]
        self.fichas_j4 = [self.j4f1, self.j4f2, self.j4f3, self.j4f4]
        
        # Diccionario de fichas por jugador
        self.fichas_jugadores = {
            1: self.fichas_j1,
            2: self.fichas_j2,
            3: self.fichas_j3,
            4: self.fichas_j4
        }
        
        # Lista de casillas (QLabel)
        self.casillas = [getattr(self, f"l{i}") for i in range(1, 69)]
        self.casillas_j1 = [getattr(self, f"j1l{i}") for i in range(69, 76)] + [self.meta]
        self.casillas_seguro = {1, 8, 13, 18, 25, 30, 35, 42, 47, 52, 59, 64}

        # Diccionario labels de la cárcel para cada jugador
        self.carcel_jugadores = {
            1: self.label_2,  # Cárcel del jugador 1
            2: self.label_71, # Cárcel del jugador 2
            3: self.label_55, # Cárcel del jugador 3
            4: self.label_35  # Cárcel del jugador 4
        }

        # Variables de estado del juego
        self.fichas_fuera = {1: [], 2: [], 3: [], 4: []}  # Fichas fuera de la cárcel por jugador
        self.valores_dados = []  # Valores de los dados lanzados
        self.posiciones_fichas = {}  # Posiciones actuales de las fichas
        self.combo_actual = None  # ComboBox para seleccionar movimientos
        self.bloqueo_movido = False  # Indica si se movió una ficha bloqueada
        self.turno_actual = 1  # Turno actual (1 a 4)
        self.pares_consecutivos = {1: 0, 2: 0, 3: 0, 4: 0}  # Contador de pares consecutivos por jugador
        self.ultima_ficha_movida = {1: None, 2: None, 3: None, 4: None}  # Última ficha movida por jugador

        # Definir las casillas de salida para cada jugador
        self.casillas_salida = {
            1: 1,   # Jugador 1 sale de l1
            2: 18,  # Jugador 2 sale de l18
            3: 35,  # Jugador 3 sale de l35
            4: 52   # Jugador 4 sale de l52
        }

        # Definir el recorrido de las fichas
        self.recorrido = {i: i+1 for i in range(1, 68)}
        self.recorrido[64] = "j1l69"
        self.recorrido.update({f"j1l{i}": f"j1l{i+1}" for i in range(69, 75)})
        self.recorrido["j1l75"] = "meta"

        # Conectar el evento clicked de todas las fichas
        for jugador, fichas in self.fichas_jugadores.items():
            for ficha in fichas:
                ficha.clicked.connect(lambda _, f=ficha: self.seleccionar_movimiento(f))

    def cambiar_turno(self):
        """Cambia el turno al siguiente jugador."""
        self.turno_actual = self.turno_actual % 4 + 1
        print(f"Turno del jugador {self.turno_actual}")

    def lanzar_dados(self):
        """Lanza los dados y actualiza la interfaz."""
        dado1, dado2 = random.randint(1, 6), random.randint(1, 6)
        print(f"Dados: {dado1}, {dado2}")

        self.valores_dados = [dado1, dado2]
        self.bloqueo_movido = False
        
        # Actualizar las imágenes de los dados
        self.ldado_1.setPixmap(QPixmap(f"dado{dado1}.png"))
        self.ldado_2.setPixmap(QPixmap(f"dado{dado2}.png"))
        self.ldado_1.setScaledContents(True)
        self.ldado_2.setScaledContents(True)
        
        # Verificar si se sacó un par
        if dado1 == dado2:
            self.pares_consecutivos[self.turno_actual] += 1
            print(f"Pares consecutivos: {self.pares_consecutivos[self.turno_actual]}")
            
            # Verificar si el jugador sacó 3 pares seguidos
            if self.pares_consecutivos[self.turno_actual] == 3:
                print(f"¡Jugador {self.turno_actual} sacó 3 pares seguidos!")
                if self.ultima_ficha_movida[self.turno_actual]:
                    self.enviar_a_carcel(self.ultima_ficha_movida[self.turno_actual])
                self.pares_consecutivos[self.turno_actual] = 0  # Reiniciar el contador
        else:
            self.pares_consecutivos[self.turno_actual] = 0  # Reiniciar el contador si no es par
        
        # Intentar sacar una ficha de la cárcel
        self.sacar_ficha_de_carcel(dado1, dado2)
        
        # Forzar movimiento si los dados son pares
        if dado1 == dado2:
            self.forzar_movimiento_bloqueo(dado1)

    def forzar_movimiento_bloqueo(self, valor):
        """Mueve una ficha bloqueada si es necesario."""
        for casilla in self.casillas:
            fichas_en_casilla = [f for f in self.fichas_fuera[self.turno_actual] if self.posiciones_fichas.get(f) == casilla]
            if len(fichas_en_casilla) == 2:
                ficha_a_mover = fichas_en_casilla[0]
                self.mover_ficha(ficha_a_mover, valor, None)
                self.bloqueo_movido = True
                return

    def sacar_ficha_de_carcel(self, dado1, dado2):
        """Saca una ficha de la cárcel si se cumple la condición."""
        casilla_salida = self.casillas_salida[self.turno_actual]
        fichas_en_salida = [f for f in self.fichas_fuera[self.turno_actual] if self.posiciones_fichas.get(f) == casilla_salida]
    
        # No permitir más de two fichas en la casilla de salida
        if len(fichas_en_salida) >= 2:
            return  
    
        fichas_a_sacar = 0
        
        if len(self.fichas_fuera[self.turno_actual]) < 4:
            if dado1 == 5 and len(fichas_en_salida) < 2:
                fichas_a_sacar += 1
                self.valores_dados.remove(5)
            if dado2 == 5 and len(fichas_en_salida) < 2:
                fichas_a_sacar += 1
                self.valores_dados.remove(5)
            if dado1 + dado2 == 5 and len(fichas_en_salida) < 2:
                fichas_a_sacar = 1
                self.valores_dados.clear()
    
        for _ in range(fichas_a_sacar):
            ficha = next((f for f in self.fichas_jugadores[self.turno_actual] if f not in self.fichas_fuera[self.turno_actual]), None)
            if ficha:
                pos_salida = self.casillas[casilla_salida - 1].pos()
                
                # Determinar si la casilla de salida es horizontal o vertical
                jugadores_con_salida_horizontal = {2, 4}  
                es_horizontal = self.turno_actual in jugadores_con_salida_horizontal
    
                # Definir offsets de desplazamiento
                offsets = [(10, 0), (40, 0)] if es_horizontal else [(0, 10), (0, 40)]
    
                # Calcular posición con desplazamiento
                x, y = pos_salida.x(), pos_salida.y()
                offset_x, offset_y = offsets[len(fichas_en_salida) % 2]  # Espaciado según las fichas en la casilla
                ficha.move(x + offset_x, y + offset_y)
    
                # Registrar la ficha fuera de la cárcel
                self.fichas_fuera[self.turno_actual].append(ficha)
                self.posiciones_fichas[ficha] = casilla_salida  
                fichas_en_salida.append(ficha)

    def seleccionar_movimiento(self, ficha):
        """Selecciona una ficha para mover."""
        # Verificar si la ficha pertenece al jugador actual
        jugador_ficha = next((jugador for jugador, fichas in self.fichas_jugadores.items() if ficha in fichas), None)
        if jugador_ficha != self.turno_actual or ficha not in self.fichas_fuera[self.turno_actual] or not self.valores_dados:
            return
        
        valores_validos = [v for v in self.valores_dados if self.puede_mover(ficha, v)]
        
        if not valores_validos:
            print("No puedes mover esta ficha.")
            return

        if self.combo_actual:
            self.combo_actual.hide()
            self.combo_actual.deleteLater()
            self.combo_actual = None

        if len(valores_validos) == 1:
            self.mover_ficha(ficha, valores_validos[0], None)
        else:
            combo = QComboBox(self)
            combo.addItems([str(v) for v in valores_validos])
            combo.move(ficha.x() + 30, ficha.y())
            combo.show()
            self.combo_actual = combo
            combo.activated.connect(lambda index, c=combo, f=ficha: self.mover_ficha(f, int(c.itemText(index)), c))

    def puede_mover(self, ficha, valor):
        """Verifica si una ficha puede moverse."""
        pos_actual = self.posiciones_fichas.get(ficha, self.casillas_salida[self.turno_actual])
        for _ in range(valor):
            siguiente_pos = self.recorrido.get(pos_actual, pos_actual)
            # Verificar todas las fichas en el tablero, no solo las del jugador actual
            fichas_en_casilla = [f for f in self.fichas_fuera[1] + self.fichas_fuera[2] + self.fichas_fuera[3] + self.fichas_fuera[4] if self.posiciones_fichas.get(f) == siguiente_pos]
            if len(fichas_en_casilla) == 2:
                return False  # Bloqueo: no se puede avanzar más allá de esta casilla
            pos_actual = siguiente_pos
        return True

    def mover_ficha(self, ficha, valor, combo):
        """Mueve una ficha a una nueva posición."""
        if combo:
            combo.hide()
            self.combo_actual = None
        self.valores_dados.remove(valor)
        
        pos_actual = self.posiciones_fichas.get(ficha, self.casillas_salida[self.turno_actual])
        for _ in range(valor):
            pos_actual = self.recorrido.get(pos_actual, pos_actual)

        # Verificar si la nueva posición es una casilla segura
        if pos_actual in self.casillas_seguro:
            fichas_en_casilla = [f for f in self.fichas_fuera[1] + self.fichas_fuera[2] + self.fichas_fuera[3] + self.fichas_fuera[4] if self.posiciones_fichas.get(f) == pos_actual]
            if len(fichas_en_casilla) >= 2:
                print("No se puede mover a una casilla segura con más de dos fichas.")
                return

        # Verificar si la nueva posición tiene una ficha de otro jugador
        fichas_en_casilla = [f for f in self.fichas_fuera[1] + self.fichas_fuera[2] + self.fichas_fuera[3] + self.fichas_fuera[4] if self.posiciones_fichas.get(f) == pos_actual]
        for otra_ficha in fichas_en_casilla:
            if otra_ficha not in self.fichas_jugadores[self.turno_actual]:
                # Solo enviar a la cárcel si la casilla no es segura
                if pos_actual not in self.casillas_seguro:
                    self.enviar_a_carcel(otra_ficha)

        self.posiciones_fichas[ficha] = pos_actual  
        nueva_casilla = self.casillas[pos_actual - 1] if isinstance(pos_actual, int) else getattr(self, pos_actual)
        
        offsets = [(10, 0), (40, 0)] if nueva_casilla.width() > nueva_casilla.height() else [(0, 10), (0, 40)]
        x, y = nueva_casilla.x(), nueva_casilla.y()
        offset_x, offset_y = offsets[len([f for f in self.fichas_fuera[self.turno_actual] if self.posiciones_fichas[f] == pos_actual]) % 2]
        ficha.move(x + offset_x, y + offset_y)

        # Registrar la última ficha movida
        self.ultima_ficha_movida[self.turno_actual] = ficha

    def enviar_a_carcel(self, ficha):
        """Envía una ficha a la cárcel."""
        jugador_ficha = next((jugador for jugador, fichas in self.fichas_jugadores.items() if ficha in fichas), None)
        if jugador_ficha:
            self.fichas_fuera[jugador_ficha].remove(ficha)
            self.posiciones_fichas[ficha] = None

            # Obtener la label de la cárcel correspondiente al jugador
            carcel_label = self.carcel_jugadores[jugador_ficha]
            carcel_pos = carcel_label.pos()
            carcel_size = carcel_label.size()

            # Calcular la posición dentro de la label de la cárcel
            fichas_en_carcel = [f for f in self.fichas_jugadores[jugador_ficha] if f not in self.fichas_fuera[jugador_ficha]]
            num_fichas_en_carcel = len(fichas_en_carcel)

            # Definir offsets para distribuir las fichas dentro de la cárcel
            offset_x = (num_fichas_en_carcel % 2) * 20  # Espaciado horizontal
            offset_y = (num_fichas_en_carcel // 2) * 20  # Espaciado vertical

            # Mover la ficha a la posición dentro de la cárcel
            ficha.move(carcel_pos.x() + offset_x, carcel_pos.y() + offset_y)
            print(f"Ficha {ficha.objectName()} enviada a la cárcel del jugador {jugador_ficha}.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MiVentana()
    ventana.show()
    sys.exit(app.exec_())