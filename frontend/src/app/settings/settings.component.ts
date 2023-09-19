import { Component } from '@angular/core';
import { ApiService } from '../api.service';
import { LoaderService } from '../loader.service';

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
    private loaderService: LoaderService) { } // Inject ApiService

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
    this.apiService.toggleNightVision().subscribe(() => {
      this.nightVision = !this.nightVision;
    });
  }

  toggleFacialDetection() {
    this.apiService.toggleFacialRecognition().subscribe(() => {
      this.facialDetection = !this.facialDetection;
    });
  }

  saveSettings() {
    const settings = {
      nightVision: this.nightVision,
      facialDetection: this.facialDetection,
      notificationCooldown: this.notificationCooldown
    };

    this.apiService.updateSystemSettings(settings).subscribe(() => {
      console.log('Success!')
    });
  }
}
