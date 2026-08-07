from fastapi import FastAPI

app = FastAPI(title='Reachy Motor Control API')

@app.get('/')
def root():
    return {'status': 'online', 'robot': 'Reachy Mini', 'motors': 8}

@app.post('/move')
def move_motor(motor_id: int, position_deg: float):
    return {'motor_id': motor_id, 'target_position': position_deg, 'status': 'moving'}
