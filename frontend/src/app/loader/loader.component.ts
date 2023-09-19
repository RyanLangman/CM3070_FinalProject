import { Component } from '@angular/core';
import { LoaderService } from '../loader.service';

@Component({
  selector: 'app-loader-component',
  template: `
    <div *ngIf="isLoading" class="loader-overlay">
      <div class="loader">Loading...</div>
    </div>
  `,
  styleUrls: ['./loader.component.scss']
})
export class LoaderComponent {
  isLoading: boolean = false;

  constructor(private loaderService: LoaderService) {
    this.loaderService.isLoading$.subscribe((loading) => {
      this.isLoading = loading;
    });
  }
}
