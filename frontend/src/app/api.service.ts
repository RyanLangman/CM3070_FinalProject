import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private ws: WebSocket | undefined;
  public imageSubject = new Subject<string>();
  private baseUrl: string = 'http://127.0.0.1:8000/api/v1';

  constructor(private http: HttpClient) { }

  connectToWebsocket(): void {
    this.ws = new WebSocket('ws://localhost:8000/api/v1/ws');

    this.ws.addEventListener('message', (event) => {
      this.imageSubject.next('data:image/jpeg;base64,' + event.data);
    });
  }

  disconnectWebsocket(): void {
    if (this.ws) {
      this.ws.close();
    }
  }

  getVideoFeed(): Observable<any> {
    return this.http.get(`${this.baseUrl}/video_feed`);
  }

  getSystemSettings(): Observable<any> {
    return this.http.get(`${this.baseUrl}/settings`);
  }

  toggleObjectDetection(): Observable<any> {
    return this.http.post(`${this.baseUrl}/toggle_object_detection`, {});
  }

  toggleFacialRecognition(): Observable<any> {
    return this.http.post(`${this.baseUrl}/toggle_facial_recognition`, {});
  }

  toggleFallDetection(): Observable<any> {
    return this.http.post(`${this.baseUrl}/toggle_fall_detection`, {});
  }
}
