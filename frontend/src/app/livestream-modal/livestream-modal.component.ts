import { Component, Input, OnDestroy } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ApiService } from '../api.service';

@Component({
  selector: 'app-livestream-modal',
  templateUrl: './livestream-modal.component.html',
  styleUrls: ['./livestream-modal.component.scss']
})
export class LivestreamModalComponent implements OnDestroy {
  @Input() cameraId: number | undefined;
  liveImageSrc: string | undefined; // Update this dynamically via a WebSocket or other method
  private ws: WebSocket | undefined;

  constructor(public activeModal: NgbActiveModal, private apiService: ApiService) {}

  ngOnInit(): void {
    if (this.cameraId !== undefined) {
      this.ws = this.apiService.getWebSocket(this.cameraId);

      this.ws.addEventListener('message', (event) => {
        console.log('Test from websocket', event);
        this.liveImageSrc = 'data:image/jpeg;base64,' + event.data;
      });
    }
  }

  closeModal() {
    this.activeModal.close();
    this.disconnectWebSocket();
  }

  ngOnDestroy(): void {
    this.disconnectWebSocket();
  }

  private disconnectWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = undefined;
    }
  }
}
