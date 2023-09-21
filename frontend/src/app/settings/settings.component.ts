import { Component } from '@angular/core';
import { ApiService } from '../api.service';
import { LoaderService } from '../loader.service';
import { ToastService } from '../toast.service';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent {
  nightVision: boolean | undefined; // Initialize with "Disable"
  facialDetection: boolean | undefined; // Initialize with "Disable"
  notificationCooldown: Number | undefined; // Initialize with the minimum value (5 seconds)

  constructor(private apiService: ApiService,
    private loaderService: LoaderService,
    public toastService: ToastService) { } // Inject ApiService

  ngOnInit(): void {
    this.loaderService.show();

    this.apiService.getSystemSettings().subscribe((settings) => {
      this.nightVision = settings.NightVisionEnabled;
      this.facialDetection = settings.FacialRecognitionEnabled;
      this.notificationCooldown = settings.NotificationCooldown;

      this.loaderService.hide();
    });
  }

  toggleNightVision() {
    let previous = this.nightVision;
    this.apiService.toggleNightVision().subscribe({
      next: () => {
        this.toastService.show("Nightvision updated.", { classname: 'bg-success text-light', delay: 5000 });
      },
      error: (err) => {
        console.error('An error occurred:', err);
        this.toastService.show("Nightvision failed to update.", { classname: 'bg-danger text-light', delay: 3000000 });
        this.nightVision = previous;
      }
    });
  }

  toggleFacialDetection() {
    let previous = this.facialDetection;
    this.apiService.toggleFacialRecognition().subscribe({
      next: () => {
        this.toastService.show("Facial Detection updated.", { classname: 'bg-success text-light', delay: 5000 });
      },
      error: (err) => {
        console.error('An error occurred:', err);
        this.toastService.show("Facial Detection failed to update.", { classname: 'bg-danger text-light', delay: 5000 });
        this.facialDetection = previous;
      }
    });
  }

  saveNotificationCooldown() {
    const settings = {
      notificationCooldown: this.notificationCooldown
    };

    let previous = this.notificationCooldown;
    this.apiService.saveNotificationCooldown(settings).subscribe({
      next: () => {
        this.toastService.show("Notification cooldown updated.", { classname: 'bg-success text-light', delay: 5000 });
      },
      error: (err) => {
        console.error('An error occurred:', err);
        this.toastService.show("Notification cooldown failed to update.", { classname: 'bg-danger text-light', delay: 5000 });
        this.notificationCooldown = previous;
      }
    });
  }
}
