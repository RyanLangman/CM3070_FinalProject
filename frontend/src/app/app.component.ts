import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ApiService } from './api.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  imageSrc: string | undefined;
  private imageSubscription: Subscription;

  constructor(private apiService: ApiService) {
    this.imageSubscription = this.apiService.imageSubject.subscribe(image => {
      this.imageSrc = image;
    });
  }

  connectToWebsocket(): void {
    this.apiService.connectToWebsocket();
  }

  disconnectWebsocket(): void {
    this.apiService.disconnectWebsocket();
  }

  ngOnDestroy(): void {
    this.imageSubscription.unsubscribe();
  }
}
