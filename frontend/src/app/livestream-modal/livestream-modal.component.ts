import { Component, Input, OnDestroy } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ApiService } from '../api.service';

interface CameraPreview {
  cameraId: number;
  frame: string;
  isMonitoring: boolean;
}

@Component({
  selector: 'app-livestream-modal',
  templateUrl: './livestream-modal.component.html',
  styleUrls: ['./livestream-modal.component.scss']
})
export class LivestreamModalComponent implements OnDestroy {
  @Input() camera: CameraPreview | undefined;
  liveImageSrc: string | undefined; // Update this dynamically via a WebSocket or other method
  private ws: WebSocket | undefined;

  constructor(public activeModal: NgbActiveModal, private apiService: ApiService) { }

  ngOnInit(): void {
    if (this.camera !== undefined && this.camera.isMonitoring) {
      this.ws = this.apiService.getWebSocket(this.camera.cameraId);

      this.ws.addEventListener('message', (event) => {
        this.liveImageSrc = 'data:image/jpeg;base64,' + event.data;
      });
    }
    else {
      
      this.ws = this.apiService.getPreviewWebsocket(this.camera!.cameraId);

      this.ws.addEventListener('message', (event) => {
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
