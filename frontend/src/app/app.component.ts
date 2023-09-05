import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ApiService } from './api.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'frontend';
  
  constructor(private apiService: ApiService) { }

  getVideoFeed() {
    this.apiService.getVideoFeed().subscribe(data => {
      console.log(data);
    });
  }

  getSystemSettings() {
    this.apiService.getSystemSettings().subscribe(data => {
      console.log(data);
    });
  }
}
