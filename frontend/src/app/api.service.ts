import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private ws: WebSocket | undefined;
  public imageSubject = new Subject<string>();
  private baseUrl: string = 'http://localhost:8000/api/v1';

  constructor(private http: HttpClient) { }

  connectToWebsocket(): void {
    this.ws = new WebSocket('ws://localhost:8000/api/v1/ws');

    this.ws.addEventListener('message', (event) => {
      this.imageSubject.next('data:image/jpeg;base64,' + event.data);
    });
  }

  disconnectWebsocket(): void {
    if (this.ws) {
      this.ws.send("closing");
      this.ws.close();
    }
  }

  getVideoFeedPreviews(): Observable<any> {
    return this.http.get(`${this.baseUrl}/video_feed_previews`);
  }

  startMonitoring(cameraId: number): Observable<any> {
    return this.http.post(`${this.baseUrl}/start_monitoring/${cameraId}`, {});
  }

  stopMonitoring(cameraId: number): Observable<any> {
    return this.http.post(`${this.baseUrl}/stop_monitoring/${cameraId}`, {});
  }

  getSystemSettings(): Observable<any> {
    return this.http.get(`${this.baseUrl}/settings`);
  }

  saveNotificationCooldown(notificationCooldown: any): Observable<any> {
    const params = new HttpParams().set('notificationCooldown', notificationCooldown.toString());
    return this.http.post(`${this.baseUrl}/set_notification_cooldown`, null, { params });
  }

  toggleFacialRecognition(): Observable<any> {
    return this.http.post(`${this.baseUrl}/toggle_facial_recognition`, {});
  }

  toggleNightVision(): Observable<any> {
    return this.http.post(`${this.baseUrl}/toggle_night_vision`, {});
  }

  getRecordings(): Observable<any> {
    return this.http.get(`${this.baseUrl}/recordings`);
  }

  deleteRecording(date: string, filename: string): Observable<any> {
    return this.http.delete(`${this.baseUrl}/recordings/${date}/${filename}`);
  }

  getWebSocket(cameraId: number): WebSocket {
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/${cameraId}`);
    return ws;
  }

  getPreviewWebsocket(cameraId: number): WebSocket {
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/${cameraId}/preview`);
    return ws;
  }
}
