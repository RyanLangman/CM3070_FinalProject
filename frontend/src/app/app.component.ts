import { Component, OnInit, OnDestroy } from '@angular/core';
import { ApiService } from './api.service';
import { LivestreamModalComponent } from './livestream-modal/livestream-modal.component';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

// Define the VideoPreviews type
interface VideoPreviews {
  frames: { [key: number]: string };  // Dictionary of webcam IDs to base64 encoded frame strings
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit, OnDestroy {
  imageSrc: string | undefined;
  videoPreviews: VideoPreviews;
  isMonitoring: { [key: number]: boolean } = {};

  constructor(private apiService: ApiService, private modalService: NgbModal) {
    this.videoPreviews = { frames: {} };
  }

  ngOnInit(): void {  // OnInit lifecycle hook added
    this.getCamerasAndVideoFeedPreviews();
  }

  getCamerasAndVideoFeedPreviews(): void {
    this.apiService.getVideoFeedPreviews().subscribe(response => {
      console.log(response);
      this.videoPreviews = response as VideoPreviews;  // Store the data
    });
  }
  
  startMonitoring(cameraId: number): void {
    this.apiService.startMonitoring(cameraId).subscribe(response => {
      this.isMonitoring[cameraId] = true;
    });
  }

  stopMonitoring(cameraId: number): void {
    this.apiService.stopMonitoring(cameraId).subscribe(response => {
      this.isMonitoring[cameraId] = false;
    });
  }

  viewLive(cameraId: number): void {
    const modalRef = this.modalService.open(LivestreamModalComponent);
    modalRef.componentInstance.cameraId = cameraId;
  }

  ngOnDestroy(): void {
  }
}
