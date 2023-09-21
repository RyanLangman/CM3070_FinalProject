import { Component, OnInit, OnDestroy } from '@angular/core';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { ApiService } from '../api.service';
import { LivestreamModalComponent } from '../livestream-modal/livestream-modal.component';
import { LoaderService } from '../loader.service';
import { ToastService } from '../toast.service';
import { faGear } from '@fortawesome/free-solid-svg-icons';

interface CameraPreview {
  cameraId: number;
  frame: string;
  isMonitoring: boolean;
}

interface Previews {
  cameraPreviews: CameraPreview[];
}

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent {
  imageSrc: string | undefined;
  previews: Previews | undefined;
  isMonitoring: { [key: number]: boolean } = {};
  loading: boolean = false;
  faGear = faGear;

  constructor(private apiService: ApiService, 
    private modalService: NgbModal,
    private loaderService: LoaderService,
    private toastService: ToastService) {
  }

  ngOnInit(): void {
    this.getCamerasAndVideoFeedPreviews();
  }

  getCamerasAndVideoFeedPreviews(): void {
    this.loading = true;

    this.apiService.getVideoFeedPreviews().subscribe({
      next: (response) => {
        this.previews = response;
        this.loading = false;
      },
      error: (err) => {
        this.toastService.show("Failed getting cameras.", { classname: 'bg-danger text-light', delay: 5000 });
        this.loaderService.hide();
        this.loading = false;
      }
    });
  }

  startMonitoring(cameraId: number): void {
    this.apiService.startMonitoring(cameraId).subscribe(() => {
      const cameraPreview = this.previews?.cameraPreviews.find(preview => preview.cameraId === cameraId);
      if (cameraPreview) {
        cameraPreview.isMonitoring = true;
      }
    });
  }

  stopMonitoring(cameraId: number): void {
    this.apiService.stopMonitoring(cameraId).subscribe(() => {
      const cameraPreview = this.previews?.cameraPreviews.find(preview => preview.cameraId === cameraId);
      if (cameraPreview) {
        cameraPreview.isMonitoring = false;
      }
    });
  }

  view(camera: CameraPreview): void {
    const modalRef = this.modalService.open(LivestreamModalComponent);
    modalRef.componentInstance.camera = camera;
  }

  ngOnDestroy(): void {
  }
}
